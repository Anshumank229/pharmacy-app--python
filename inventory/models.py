# inventory/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Medicine(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='medicines')
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True, null=True)
    dosage_form = models.CharField(max_length=50, blank=True, help_text="e.g. Tablet, Capsule, Syrup")
    strength = models.CharField(max_length=50, blank=True, help_text="e.g. 500mg, 10ml")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='medicines/', null=True, blank=True)
    requires_prescription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name'], name='medicine_name_idx'),
            models.Index(fields=['category'], name='medicine_category_idx'),
        ]

    def __str__(self):
        return self.name


class MedicineBatch(models.Model):
    """Tracks stock batches per medicine with expiry dates."""
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField()
    manufacturing_date = models.DateField(blank=True, null=True)
    supplier = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']
        verbose_name = "Medicine Batch"
        verbose_name_plural = "Medicine Batches"

    def __str__(self):
        return f"{self.medicine.name} — Batch {self.batch_number} (exp: {self.expiry_date})"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        delta = self.expiry_date - timezone.now().date()
        return delta.days

    @property
    def expiry_status(self):
        days = self.days_until_expiry
        if days < 0:
            return "EXPIRED"
        elif days <= 30:
            return "EXPIRING_SOON"
        return "OK"


class ServiceArea(models.Model):
    pincode = models.CharField(max_length=10, unique=True)
    area_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pincode} — {self.area_name}"

    class Meta:
        verbose_name = "Service Area"
        verbose_name_plural = "Service Areas"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    area_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile — {self.user.email}"


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"

    @property
    def is_valid(self):
        return self.is_active and self.times_used < self.max_uses


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15, default='')
    delivery_address = models.TextField(default='')
    pincode = models.CharField(max_length=10, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    discount_applied = models.PositiveIntegerField(default=0)
    prescription_image = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['customer_email'], name='order_email_idx'),
            models.Index(fields=['status'], name='order_status_idx'),
            models.Index(fields=['created_at'], name='order_created_idx'),
            models.Index(fields=['pincode'], name='order_pincode_idx'),
        ]

    def __str__(self):
        return f"Order #{self.id} by {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time_of_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.medicine.name} (Order #{self.order.id})"


class Review(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='reviews')
    customer_name = models.CharField(max_length=255)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer_name} for {self.medicine.name}"