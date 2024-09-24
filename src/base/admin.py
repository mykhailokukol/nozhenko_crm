import locale
from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from base import models, forms


try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except locale.Error:
    print("Не удалось установить локаль, используем локаль по умолчанию.")


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


# Inlines
class StorageClientM2MInline(admin.TabularInline):
    model = models.StorageClientM2M
    extra = 1


class ItemImageInline(admin.TabularInline):
    model = models.ItemImage
    max_num = 5
    fields = ["image_tag", "image"]
    readonly_fields = ["image_tag"]
    
    def get_min_num(self, request, obj=None, **kwargs):
        if self.parent_model == models.ItemStock:
            return 0
        return 1

    def get_extra(self, request, obj=None, **kwargs):
        if self.parent_model == models.ItemStock:
            return 5
        return 4


class ItemBookingItemM2MInline(admin.TabularInline):
    model = models.ItemBookingItemM2M
    min_num = 1
    extra = 0
    validate_min = True
    
    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js",
            "admin/js/check_item_booking.js",
        )


class RecoveryImageInline(admin.TabularInline):
    model = models.RecoveryImage
    extra = 4
    min_num = 1
    max_num = 5
    validate_min = True
    fields = ["image_tag", "image"]
    readonly_fields = ["image_tag"]


class ItemRefundItemM2MInline(admin.TabularInline):
    model = models.ItemRefundItemM2M
    min_num = 1
    extra = 0
    validate_min = True


# Models
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
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.groups.filter(name="Кладовщик").exists():
            queryset = request.user.storages.all()
            return queryset
        return super().get_queryset(request)


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
    list_display = ["article", "name", "count", "is_booked_display"]
    exclude = ["id"]
    search_fields = ["article", "name"]
    readonly_fields = ["article", "is_booked_display", "booking_projects", "booking_quantities", "booking_periods"]
    inlines = [ItemImageInline]
    
    @admin.display(description="Забронирован?")
    def is_booked_display(self, obj):
        result = {True: "Да", False: "Нет"}
        return result[obj.bookings.exists()]

    @admin.display(description="Проекты")
    def booking_projects(self, obj):
        projects = obj.bookings.values_list('project__name', flat=True).distinct()
        return ", ".join(projects) if projects else "—"

    @admin.display(description="Количество")
    def booking_quantities(self, obj):
        booking_items = models.ItemBookingItemM2M.objects.filter(item=obj)
        quantities = [bi.item_count for bi in booking_items]
        return sum(quantities) if quantities else "—"

    @admin.display(description="Периоды брони")
    def booking_periods(self, obj):
        periods = obj.bookings.values_list('start_date', 'end_date')
        return " | ".join([
            f"{start.strftime('%d %B %Y')} - {end.strftime('%d %B %Y')}" for start, end in periods
        ]) if periods else "—"
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        return queryset.filter(count__gt=0)


@admin.register(models.ItemStock)
class AdminItemStock(admin.ModelAdmin):
    list_display = ["client_display", "storage_display", "article_display", "count"]
    list_filter = ('request_type',)
    search_fields = ('new_item_name', 'existing_item__name')
    inlines = [ItemImageInline]
    
    @admin.display(description="Клиент")
    def client_display(self, obj):
        if obj.existing_item:
            return obj.existing_item.client or obj.existing_item.project.client
        else:
            return obj.new_item_client
    
    @admin.display(description="Склад")
    def storage_display(self, obj):
        if obj.existing_item:
            return obj.existing_item.storage
        else:
            return obj.new_item_storage
    
    @admin.display(description="Товар")
    def article_display(self, obj):
        if obj.existing_item:
            return obj.existing_item
        else:
            return obj.new_item_name
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        if request.user.groups.filter(name="Кладовщик").exists():
            fields = [
                "request_type", "existing_item", "count",
                "new_item_name", "new_item_description",
                "new_item_weight", "new_item_height",
                "new_item_width", "new_item_length",
                "new_item_project", "new_item_client",
                "new_item_storage", "new_item_category",
                "new_item_status", "new_item_arrival_date",
                "new_item_expiration_date", "planning_date",
            ]
            return fields
        else:
            return ["is_approved", "date"]
    
    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js",
            "admin/js/admin_itemstock.js",
        )


@admin.register(models.ItemBooking)
class AdminItemBooking(admin.ModelAdmin):
    list_display = ('project', 'city', 'is_approved', 'booking_items', 'booking_quantities', 'booking_periods')
    form = forms.BookingAdminForm
    exclude = ["id"]
    search_fields = ["project__name", "items__name", "start_date__month"] # TODO: add month
    inlines = [ItemBookingItemM2MInline]
    
    @admin.display(description="Товары")
    def booking_items(self, obj):
        items = obj.items.values_list('name', flat=True)
        return ", ".join(items) if items else "—"

    @admin.display(description="Количество")
    def booking_quantities(self, obj):
        booking_items = models.ItemBookingItemM2M.objects.filter(booking=obj)
        quantities = [f"{bi.item.name}: {bi.item_count}" for bi in booking_items]
        return ", ".join(quantities) if quantities else "—"

    @admin.display(description="Периоды брони")
    def booking_periods(self, obj):
        start_date = obj.start_date.strftime('%d %B %Y') if obj.start_date else "—"
        end_date = obj.end_date.strftime('%d %B %Y') if obj.end_date else "—"
        return f"{start_date} - {end_date}"
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        if request.user.groups.filter(name="Кладовщик").exists():
            fields = [
                "items", "project", "date",
                "city", "description", "start_date",
                "end_date",
            ]
            return fields
        else:
            return ["is_approved"]
    
    
@admin.register(models.ItemRecovery)
class AdminItemRecovery(admin.ModelAdmin):
    list_display = ["item", "count", "item__storage", "planning_date", "is_ceo_approved", "is_approved",]
    exclude = ["id"]
    search_fields = ["item__article", "item__name"]
    inlines = [RecoveryImageInline]
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        if request.user.groups.filter(name="Кладовщик").exists():
            fields = [
                "item", "reason", "planning_date",
                "description", "status", "is_ceo_approved"
            ]
            return fields
        elif request.user.groups.filter(name="Руководитель").exists():
            return ["is_approved", "date"]
        else:
            return ["is_approved", "is_ceo_approved", "date"]

    
@admin.register(models.ItemRefund)
class AdminItemRefund(admin.ModelAdmin):
    exclude = ["id"]
    search_fields = ["items__article", "items__name"]
    inlines = [ItemRefundItemM2MInline]
    list_display = ["project__client", "project__name", "city", "date", "storages_display"]
    
    @admin.display(description="Склады")
    def storages_display(self, obj):
        return " | ".join([item.storage.name for item in obj.items.all()])
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        if request.user.groups.filter(name="Кладовщик").exists():
            fields = [
                "items", "project", "status", "description",
            ]
            return fields
        else:
            return ["is_approved"]
    

@admin.register(models.ItemConsumption)
class AdminItemConsumption(admin.ModelAdmin):
    list_display = ["booking__project__client", "booking__project", "city", "date_display", "storage_display"]
    exclude = ["id"]
    search_fields = ["booking__items__article", "booking__items__name", "date__month"]
    
    @admin.display(description="Дата отправки")
    def date_display(self, obj):
        return obj.date.strftime('%d %B %Y') if obj.date else ""
    
    @admin.display(description="Склады")
    def storage_display(self, obj):
        return ", ".join([str(item.storage) for item in obj.booking.items.all()])
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        if request.user.groups.filter(name="Кладовщик").exists():
            return ["booking", "date_created"]
        else:
            return ["date_created", "is_approved"]
    
    