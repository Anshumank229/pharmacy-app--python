# inventory/models.py
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="medicines")

    dosage_form = models.CharField(max_length=50, help_text="e.g., Tablet, Capsule, Syrup")
    strength = models.CharField(max_length=50, help_text="e.g., 500mg, 10ml")
    description = models.TextField(blank=True, null=True)

    # --- NEW IMAGE FIELD ---
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    # --- PRESCRIPTION REQUIREMENT ---
    requires_prescription = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.strength})"


class Order(models.Model):
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # --- PRESCRIPTION IMAGE PATH ---
    prescription_image = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time_of_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.medicine.name} (Order #{self.order.id})"
# Add this to the bottom of inventory/models.py

class Review(models.Model):
    medicine = models.ForeignKey(Medicine, related_name='reviews', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}⭐ for {self.medicine.name} by {self.customer_name}"