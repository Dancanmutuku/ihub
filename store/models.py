from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User

# =========================
# CATEGORY MODEL
# =========================
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    icon = models.CharField(
        max_length=50,
        default='bi-cpu',
        help_text='Bootstrap Icons class'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:category", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    # =========================
    # Relationships
    # =========================
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='products'
    )

    # =========================
    # Core Fields
    # =========================
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Set if product is on sale"
    )

    image_url = models.URLField(max_length=500, blank=True)

    # =========================
    # Inventory & Availability
    # =========================
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    new_arrival = models.BooleanField(default=False)
    brand = models.CharField(max_length=100, blank=True)

    # =========================
    # Specifications
    # =========================
    specs = models.JSONField(default=dict, blank=True, help_text="Key-value product specifications")

    # =========================
    # Timestamps
    # =========================
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # =========================
    # Metadata
    # =========================
    class Meta:
        ordering = ['-created', '-id']

    # =========================
    # String Representation
    # =========================
    def __str__(self):
        return self.name

    # =========================
    # URL Helper
    # =========================
    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    # =========================
    # Override Save
    # =========================
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # =========================
    # Computed Properties
    # =========================
    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int((self.original_price - self.price) / self.original_price * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0
# =========================
# REVIEW MODEL
# =========================
class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    comment = models.TextField()

    class Meta:
        ordering = ["-id"]
        unique_together = ["product", "user"]

    def __str__(self):
        return f"{self.user.username} – {self.product.name} ({self.rating}★)"