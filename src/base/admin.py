from django.contrib import admin, messages
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from admin_extra_buttons.api import ExtraButtonsMixin

from base import models, forms


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


@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["article", "name", "is_booked", "expiration_date"]
    exclude = ["id"]
    search_fields = ["article", "name"]
    readonly_fields = ["article"]
    
    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        # if not self.request.user.is_superuser:
        #     self.exclude.append("is_approved")
