from django import template

register = template.Library()


@register.filter
def currency_kes(value):
    """Format value as KES currency."""
    try:
        return f"KES {float(value):,.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
def star_range(value):
    """Return range for star rating."""
    try:
        return range(1, int(value) + 1)
    except (TypeError, ValueError):
        return range(0)


@register.filter
def empty_star_range(value):
    """Return empty stars for rating."""
    try:
        return range(int(value) + 1, 6)
    except (TypeError, ValueError):
        return range(1, 6)
