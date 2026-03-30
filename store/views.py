from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg
from .models import Category, Product, Review
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def home(request):
    featured_products = Product.objects.filter(available=True, featured=True)[:8]
    new_arrivals = Product.objects.filter(available=True, new_arrival=True)[:8]
    categories = Category.objects.all()
    on_sale = Product.objects.filter(available=True, original_price__isnull=False)[:4]
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'on_sale': on_sale,
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    products = Product.objects.filter(available=True)
    category = None

    # Filters
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    sort = request.GET.get('sort', '-created')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    brand = request.GET.get('brand')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if brand:
        products = products.filter(brand__icontains=brand)

    valid_sorts = ['-created', 'price', '-price', 'name', '-name']
    if sort in valid_sorts:
        products = products.order_by(sort)

    brands = Product.objects.filter(available=True).values_list('brand', flat=True).distinct().exclude(brand='')

    context = {
        'products': products,
        'category': category,
        'search_query': search_query,
        'sort': sort,
        'brands': brands,
        'min_price': min_price,
        'max_price': max_price,
        'selected_brand': brand,
    }
    return render(request, 'store/product_list.html', context)


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)

    sort = request.GET.get('sort', '-created')
    valid_sorts = ['-created', 'price', '-price', 'name']
    if sort in valid_sorts:
        products = products.order_by(sort)

    context = {
        'category': category,
        'products': products,
        'sort': sort,
    }
    return render(request, 'store/category.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    reviews = product.reviews.select_related('user').all()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]

    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related_products': related_products,
        'user_review': user_review,
    }
    return render(request, 'store/product_detail.html', context)


@login_required
@require_POST
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if rating and comment:
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': int(rating), 'comment': comment}
        )
    from django.shortcuts import redirect
    return redirect('store:product_detail', slug=slug)


def search(request):
    query = request.GET.get('q', '')
    products = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            available=True
        )
    return render(request, 'store/search.html', {'products': products, 'query': query})
