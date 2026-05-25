# inventory/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Medicine(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='medicines')
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

    def __str__(self):
        return self.name


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
    # CharField keeps manual shutil upload in sync — ImageField would conflict
    prescription_image = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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