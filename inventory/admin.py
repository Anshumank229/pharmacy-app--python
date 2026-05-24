
from django.contrib import admin
from .models import Category, Medicine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    # This dictates which columns show up in the admin list view
    list_display = ('name', 'category', 'price', 'stock', 'requires_prescription')

    # Adds a sidebar filter panel
    list_filter = ('category', 'requires_prescription')

    # Adds a search bar at the top
    search_fields = ('name', 'brand')