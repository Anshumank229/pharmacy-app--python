# inventory/admin.py
from django.contrib import admin
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Medicine, Order, OrderItem, Review, ServiceArea, UserProfile


# ==========================================
# CATEGORY
# ==========================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_count')

    def get_queryset(self, request):
        # FIX: use 'medicines' not 'medicine_set' — matches related_name on the model
        return super().get_queryset(request).annotate(medicine_count=Count('medicines'))

    @admin.display(description='Total Medicines')
    def medicine_count(self, obj):
        return obj.medicine_count


# ==========================================
# MEDICINE
# ==========================================
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'requires_prescription')
    list_filter = ('category', 'requires_prescription')
    search_fields = ('name', 'brand')
    list_select_related = ['category']


# ==========================================
# SERVICE AREA
# ==========================================
@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'area_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('pincode', 'area_name')
    list_editable = ('is_active',)


# ==========================================
# USER + PROFILE
# ==========================================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Delivery Profile"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


# ==========================================
# ORDER
# ==========================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('medicine', 'quantity', 'price_at_time_of_purchase')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'pincode', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'pincode')
    search_fields = ('customer_name', 'customer_email', 'customer_phone', 'pincode')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]
    list_select_related = True


# ==========================================
# REVIEW
# ==========================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'medicine', 'created_at')
    list_filter = ('rating',)
    search_fields = ('customer_name',)
    list_select_related = ['medicine']