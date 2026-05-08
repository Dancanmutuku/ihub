from decimal import Decimal

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path, reverse
from django.utils import timezone

from orders.models import Order, OrderItem
from payments.models import Payment
from store.models import Category, Product, Review


User = get_user_model()


def _money(value):
    return value or Decimal("0.00")


def _percent(current, previous):
    if not previous:
        return 100 if current else 0
    return round(((current - previous) / previous) * 100, 1)


def _date_window(days):
    now = timezone.now()
    start = now - timezone.timedelta(days=days)
    previous_start = start - timezone.timedelta(days=days)
    return now, start, previous_start


def _revenue_queryset():
    line_total = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    return OrderItem.objects.filter(order__paid=True).annotate(line_total=line_total)


def insights_view(request):
    now, window_start, previous_start = _date_window(30)
    low_stock_threshold = 5

    revenue_lines = _revenue_queryset()
    revenue_total = _money(revenue_lines.aggregate(total=Sum("line_total"))["total"])
    revenue_30 = _money(
        revenue_lines.filter(order__created__gte=window_start).aggregate(total=Sum("line_total"))["total"]
    )
    revenue_previous = _money(
        revenue_lines.filter(
            order__created__gte=previous_start,
            order__created__lt=window_start,
        ).aggregate(total=Sum("line_total"))["total"]
    )

    orders_total = Order.objects.count()
    orders_30 = Order.objects.filter(created__gte=window_start).count()
    orders_previous = Order.objects.filter(
        created__gte=previous_start,
        created__lt=window_start,
    ).count()

    customers_total = User.objects.filter(is_staff=False).count()
    customers_30 = User.objects.filter(is_staff=False, date_joined__gte=window_start).count()
    customers_previous = User.objects.filter(
        is_staff=False,
        date_joined__gte=previous_start,
        date_joined__lt=window_start,
    ).count()

    products_total = Product.objects.count()
    available_products = Product.objects.filter(available=True).count()
    low_stock_products = Product.objects.filter(stock__lte=low_stock_threshold).count()
    out_of_stock_products = Product.objects.filter(stock=0).count()

    status_counts = {
        row["status"]: row["count"]
        for row in Order.objects.values("status").annotate(count=Count("id"))
    }
    payment_counts = {
        row["status"]: row["count"]
        for row in Payment.objects.values("status").annotate(count=Count("id"))
    }

    top_products = (
        revenue_lines.values("product_name")
        .annotate(units=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-revenue")[:8]
    )
    recent_orders = (
        Order.objects.select_related("user")
        .prefetch_related("items")
        .order_by("-created")[:8]
    )
    inventory_watch = Product.objects.select_related("category").filter(stock__lte=low_stock_threshold).order_by("stock", "name")[:10]
    latest_admin_logs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:8]

    daily_rows = (
        revenue_lines.filter(order__created__gte=window_start)
        .annotate(day=TruncDate("order__created"))
        .values("day")
        .annotate(revenue=Sum("line_total"), orders=Count("order", distinct=True))
        .order_by("day")
    )
    max_daily_revenue = max([row["revenue"] for row in daily_rows], default=Decimal("0.00"))
    daily_revenue = [
        {
            "day": row["day"],
            "revenue": _money(row["revenue"]),
            "orders": row["orders"],
            "bar_width": int((row["revenue"] / max_daily_revenue) * 100) if max_daily_revenue else 0,
        }
        for row in daily_rows
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Store insights",
        "subtitle": "Commercial health, operations, and inventory signals",
        "stats": [
            {
                "label": "Revenue",
                "value": f"KES {revenue_total:,.2f}",
                "detail": f"KES {revenue_30:,.2f} in the last 30 days",
                "trend": _percent(revenue_30, revenue_previous),
            },
            {
                "label": "Orders",
                "value": f"{orders_total:,}",
                "detail": f"{orders_30:,} new orders in the last 30 days",
                "trend": _percent(orders_30, orders_previous),
            },
            {
                "label": "Customers",
                "value": f"{customers_total:,}",
                "detail": f"{customers_30:,} joined in the last 30 days",
                "trend": _percent(customers_30, customers_previous),
            },
            {
                "label": "Products",
                "value": f"{available_products:,}/{products_total:,}",
                "detail": f"{low_stock_products:,} low stock, {out_of_stock_products:,} out of stock",
                "trend": None,
            },
        ],
        "status_counts": status_counts,
        "payment_counts": payment_counts,
        "top_products": top_products,
        "recent_orders": recent_orders,
        "inventory_watch": inventory_watch,
        "daily_revenue": daily_revenue,
        "latest_admin_logs": latest_admin_logs,
        "counts": {
            "categories": Category.objects.count(),
            "reviews": Review.objects.count(),
            "active_sessions": Session.objects.filter(expire_date__gte=now).count(),
            "staff_users": User.objects.filter(is_staff=True).count(),
        },
        "audit_url": reverse("admin:audit_logs"),
        "insights_url": reverse("admin:insights"),
    }
    return render(request, "admin/insights.html", context)


def audit_logs_view(request):
    logs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")
    query = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    period = request.GET.get("period", "30")

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(object_repr__icontains=query)
            | Q(change_message__icontains=query)
            | Q(content_type__app_label__icontains=query)
            | Q(content_type__model__icontains=query)
        )
    if action in {"1", "2", "3"}:
        logs = logs.filter(action_flag=int(action))
    if period in {"7", "30", "90"}:
        logs = logs.filter(action_time__gte=timezone.now() - timezone.timedelta(days=int(period)))

    action_labels = {
        1: "Added",
        2: "Changed",
        3: "Deleted",
    }
    log_rows = []
    for entry in logs[:200]:
        log_rows.append(
            {
                "entry": entry,
                "action_label": action_labels.get(entry.action_flag, "Unknown"),
                "change_message": entry.get_change_message() or "No extra details recorded.",
            }
        )

    context = {
        **admin.site.each_context(request),
        "title": "System audit logs",
        "subtitle": "Admin activity captured by Django's audit trail",
        "log_rows": log_rows,
        "query": query,
        "selected_action": action,
        "selected_period": period,
        "action_labels": action_labels,
        "total_visible": len(log_rows),
        "insights_url": reverse("admin:insights"),
        "audit_url": reverse("admin:audit_logs"),
    }
    return render(request, "admin/audit_logs.html", context)


def install_admin_dashboard():
    if getattr(admin.site, "_techstore_dashboard_installed", False):
        return

    original_get_urls = admin.site.get_urls

    def get_urls():
        custom_urls = [
            path("insights/", admin.site.admin_view(insights_view), name="insights"),
            path("audit-logs/", admin.site.admin_view(audit_logs_view), name="audit_logs"),
        ]
        return custom_urls + original_get_urls()

    admin.site.get_urls = get_urls
    admin.site.index_template = "admin/custom_index.html"
    admin.site.site_header = "TechStore administration"
    admin.site.site_title = "TechStore admin"
    admin.site.index_title = "Site administration"
    admin.site._techstore_dashboard_installed = True


install_admin_dashboard()
