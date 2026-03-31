from django.contrib import admin
from .models import Category, Product, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'featured', 'new_arrival']
    list_filter = ['available', 'featured', 'new_arrival', 'category']
    list_editable = ['price', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'brand']
    fieldsets = (
        ('Basic Info', {'fields': ('category', 'name', 'slug', 'brand', 'description')}),
        ('Pricing & Stock', {'fields': ('price', 'original_price', 'stock', 'available')}),
        ('Media', {'fields': ('image_url',)}),
        ('Flags', {'fields': ('featured', 'new_arrival')}),
        ('Specifications', {'fields': ('specs',)}),
    )
    # ✅ Remove any readonly_fields reference to 'created' or 'updated'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating']  # removed 'created'
    list_filter = ['rating']
    search_fields = ['user__username', 'product__name']