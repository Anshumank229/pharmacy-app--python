# inventory/admin.py
from django.contrib import admin
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Category, Medicine, MedicineBatch, Order, OrderItem, Review, ServiceArea, UserProfile, Coupon


# ==========================================
# CATEGORY
# ==========================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_count')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(medicine_count=Count('medicines'))

    @admin.display(description='Total Medicines')
    def medicine_count(self, obj):
        return obj.medicine_count


# ==========================================
# MEDICINE BATCH INLINE
# ==========================================
class MedicineBatchInline(admin.TabularInline):
    model = MedicineBatch
    extra = 1
    fields = ('batch_number', 'quantity', 'expiry_date', 'manufacturing_date', 'supplier', 'expiry_status_display')
    readonly_fields = ('expiry_status_display',)

    @admin.display(description='Status')
    def expiry_status_display(self, obj):
        if not obj.pk:
            return '—'
        status = obj.expiry_status
        if status == 'EXPIRED':
            return '🔴 Expired'
        elif status == 'EXPIRING_SOON':
            return f'🟡 Expires in {obj.days_until_expiry} days'
        return f'🟢 OK ({obj.days_until_expiry} days)'


# ==========================================
# MEDICINE
# ==========================================
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'requires_prescription', 'expiry_alert')
    list_filter = ('category', 'requires_prescription')
    search_fields = ('name', 'brand')
    list_select_related = ['category']
    inlines = [MedicineBatchInline]

    @admin.display(description='Batch Alert')
    def expiry_alert(self, obj):
        soon = obj.batches.filter(
            expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30),
            expiry_date__gte=timezone.now().date()
        ).count()
        expired = obj.batches.filter(expiry_date__lt=timezone.now().date()).count()
        if expired:
            return f'🔴 {expired} expired'
        if soon:
            return f'🟡 {soon} expiring soon'
        return '🟢'


# ==========================================
# MEDICINE BATCH (standalone)
# ==========================================
@admin.register(MedicineBatch)
class MedicineBatchAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'batch_number', 'quantity', 'expiry_date', 'expiry_status_display', 'supplier')
    list_filter = ('expiry_date',)
    search_fields = ('medicine__name', 'batch_number', 'supplier')
    list_select_related = ['medicine']
    date_hierarchy = 'expiry_date'

    @admin.display(description='Status')
    def expiry_status_display(self, obj):
        status = obj.expiry_status
        if status == 'EXPIRED':
            return f'🔴 Expired {abs(obj.days_until_expiry)} days ago'
        elif status == 'EXPIRING_SOON':
            return f'🟡 Expires in {obj.days_until_expiry} days'
        return f'🟢 OK'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('medicine')


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
# COUPON
# ==========================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'times_used', 'max_uses', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code',)
    list_editable = ('is_active',)
    readonly_fields = ('times_used', 'created_at')


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
    list_display = (
        'id', 'customer_name', 'customer_phone', 'pincode',
        'total_price', 'discount_applied', 'coupon_code', 'status', 'created_at'
    )
    list_filter = ('status', 'pincode')
    search_fields = ('customer_name', 'customer_email', 'customer_phone', 'pincode')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]
    list_select_related = True
    date_hierarchy = 'created_at'


# ==========================================
# REVIEW
# ==========================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'medicine', 'created_at')
    list_filter = ('rating',)
    search_fields = ('customer_name',)
    list_select_related = ['medicine']