# inventory/admin.py
from django.contrib import admin
from django.db.models import Count
from .models import Category, Medicine, Order, OrderItem, Review

# ==========================================
# CATEGORY ADMIN
# ==========================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_count')

    def get_queryset(self, request):
        # Optimizes database by counting related medicines in a single query
        # Note: Depending on your related_name setup, 'medicines' might need to be 'medicine_set'
        return super().get_queryset(request).annotate(medicine_count=Count('medicine_set'))

    @admin.display(description='Total Medicines')
    def medicine_count(self, obj):
        return obj.medicine_count

# ==========================================
# MEDICINE ADMIN
# ==========================================
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'requires_prescription')
    list_filter = ('category', 'requires_prescription')
    search_fields = ('name',)
    list_select_related = ['category']  # Prevents the N+1 database slowdown!

# ==========================================
# ORDER & ORDER ITEMS ADMIN
# ==========================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # Prevents empty blank rows from showing up
    readonly_fields = ('medicine', 'quantity', 'price_at_time_of_purchase')
    can_delete = False # Prevents accidental deletion of purchased items

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Added total_price here since we just added it to models.py!
    list_display = ('id', 'customer_name', 'customer_email', 'total_price', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer_name', 'customer_email')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]  # Injects the OrderItems directly into the Order page

# ==========================================
# REVIEW ADMIN
# ==========================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'medicine', 'created_at')
    list_filter = ('rating',)
    search_fields = ('customer_name',)
    list_select_related = ['medicine']  # Prevents the N+1 database slowdown!