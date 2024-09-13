from django.contrib import admin, messages
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from admin_extra_buttons.api import ExtraButtonsMixin

from base import models, forms
from base.utils import create_custom_permissions


create_custom_permissions()


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["username"]
    exclude = ["id", "user_permissions"]
    search_fields = ["username", "id"]
    readonly_fields = ["last_login", "is_superuser"]

    add_form = forms.CustomUserCreationForm

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return [(None, {"fields": ("username", "password")})]
        return super().get_fieldsets(request, obj)

    def add_view(self, request, form_url="", extra_context=None):
        self.fieldsets = [(None, {"fields": ("username", "password")})]
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.fieldsets = None
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
        

admin.site.register(models.User, CustomUserAdmin)


class StorageClientM2MInline(admin.TabularInline):
    model = models.StorageClientM2M
    extra = 1
    

@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name"]
    exclude = ["id"]
    search_fields = ["name"]
    inlines = [StorageClientM2MInline]


@admin.register(models.Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ["name", "free_area", "area"]
    exclude = ["id"]
    search_fields = ["name", "clients"]


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "client"]
    exclude = ["id"]
    search_fields = ["name", "client"]


@admin.register(models.ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    exclude = ["id"]
    search_fields = ["name"]


@admin.register(models.ItemStatus)
class ItemStatusAdmin(admin.ModelAdmin):
    list_display = ["text"]
    exclude = ["id"]


class ItemImageInline(admin.TabularInline):
    model = models.ItemImage
    extra = 4
    min_num = 1
    max_num = 5
    validate_min = True
    fields = ["image_tag", "image"]
    readonly_fields = ["image_tag"]


@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["article", "name", "expiration_date"]
    exclude = ["id"]
    search_fields = ["article", "name"]
    readonly_fields = ["article"]
    inlines = [ItemImageInline]
    
    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        # if not self.request.user.is_superuser:
        #     self.exclude.append("is_approved")


@admin.register(models.ItemStock)
class AdminItemStock(admin.ModelAdmin):
    list_display = ('request_type', 'existing_item', 'new_item_name', 'count')
    list_filter = ('request_type',)
    search_fields = ('new_item_name', 'existing_item__name')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.request_type == 'existing':
            return fields + ['existing_item']
        elif obj and obj.request_type == 'new':
            return fields + ['new_item_name', 'new_item_description', 'new_item_weight', 'new_item_height', 'new_item_width', 'new_item_length']
        return fields

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.request_type == 'existing':
            return ['new_item_name', 'new_item_description', 'new_item_weight', 'new_item_height', 'new_item_width', 'new_item_length']
        elif obj and obj.request_type == 'new':
            return ['existing_item']
        return super().get_readonly_fields(request, obj)


@admin.register(models.ItemBooking)
class AdminItemBooking(admin.ModelAdmin):
    form = forms.BookingAdminForm
    list_display = ["item", "count", "start_date", "end_date", "is_approved"]
    exclude = ["id"]
    search_fields = ["item__article", "item__name"]
    
    
@admin.register(models.ItemRecovery)
class AdminItemRecovery(admin.ModelAdmin):
    list_display = ["item", "is_ceo_approved", "is_approved"]
    exclude = ["id"]
    search_fields = ["item__article", "item__name"]
    
    
@admin.register(models.ItemRefund)
class AdminItemRefund(admin.ModelAdmin):
    list_display = ["item", "is_approved"]
    exclude = ["id"]
    search_fields = ["item__article", "item__name"]
    
    