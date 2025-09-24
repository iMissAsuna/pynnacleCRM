# website/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import Record, TenantImage, Property, Folder, Document, CustomUser
import os

class TenantImageInline(admin.TabularInline):
    model = TenantImage
    extra = 1
    readonly_fields = ('uploaded_at',)

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'first_name',
        'last_name',
        'occupancy_status_colored',
        'current_residence',
        'move_in_date',
    )
    list_filter = ('occupancy_status',)
    inlines = [TenantImageInline]

    def occupancy_status_colored(self, obj):
        color_map = {
            'Occupied': 'red',
            'Vacant': 'green',
            'Previous': 'gray'
        }
        status = obj.occupancy_status
        color = color_map.get(status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)

    occupancy_status_colored.short_description = 'Occupancy Status'
    occupancy_status_colored.admin_order_field = 'occupancy_status'

class FolderInline(admin.TabularInline):
    model = Folder
    extra = 1

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    readonly_fields = ('uploaded_at',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'postcode', 'property_type')
    inlines = [FolderInline, DocumentInline]
    search_fields = ('name', 'address')
    list_filter = ('property_type',)

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'property', 'parent')
    list_filter = ('property',)
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'property', 'folder', 'uploaded_at')
    list_filter = ('property', 'folder')
    search_fields = ('file',)

    def get_file_name(self, obj):
        return os.path.basename(obj.file.name)
    
    get_file_name.short_description = 'File Name'
    get_file_name.admin_order_field = 'file'

@admin.register(TenantImage)
class TenantImageAdmin(admin.ModelAdmin):
    list_display = ('record', 'category', 'uploaded_at')
    list_filter = ('category',)
    search_fields = ('record__first_name', 'record__last_name', 'description')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    pass