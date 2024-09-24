from datetime import datetime
from random import randint

from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser


def get_image_upload_path(instance, filename):
    try:
        return f"items/{instance.item.article}/{filename}"
    except AttributeError:
        try:
            return f"items/{instance.item_stock.existing_item.article}/{filename}"
        except AttributeError:
            return f"items/{instance.item_stock.new_item_name}/{filename}"


def get_recovery_item_image(instance, filename):
    return f"items/recovery/{instance.id}/{filename}"


class UserManager(BaseUserManager):
    use_in_migrations = True
    
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("Username must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)
    
    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        
        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
    
    username = models.CharField(max_length=128, verbose_name="Никнейм*", unique=True)
    password = models.CharField(max_length=255, verbose_name="Пароль*")
    
    first_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Отчество")
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Имеет доступ к сайту?",
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Руководитель/Администратор?*",
    )
    
    date_joined = models.DateField(auto_now_add=True)
    
    clients = models.ManyToManyField(
        "base.Client",
        blank=True,
        verbose_name="Клиенты",
        related_name="users",
    )
    storages = models.ManyToManyField(
        "base.Storage",
        blank=True,
        verbose_name="Склады",
        related_name="users",
    )
    
    def __str__(self) -> str:
        return f"{self.username}"
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(models.Model):
    name = models.CharField(max_length=128, verbose_name="Имя/Название*")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Storage(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название*")
    area = models.PositiveIntegerField(
        verbose_name="Площадь (кв.м.)*",
        null=True,
        blank=True,
    )
    clients = models.ManyToManyField(
        "base.Client",
        verbose_name="Клиенты",
        related_name="storages",
        through="base.StorageClientM2M"
    )
    free_area = models.PositiveIntegerField(
        verbose_name="Свободная площадь (кв.м.)",
        default=0,
        blank=True,
    )
    
    def __str__(self):
        return f"{self.name} ({self.free_area} кв.м. свободно)"
    
    def clean(self):
        if self.free_area > self.area:
            raise ValidationError(
                "Невозможно установить свободную площадь больше реальной"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"


class StorageClientM2M(models.Model):
    storage = models.ForeignKey(
        "base.Storage", 
        on_delete=models.CASCADE,
        verbose_name="Склад*",
    )
    client = models.ForeignKey(
        "base.Client", 
        on_delete=models.CASCADE,
        verbose_name="Клиент*",
    )
    booked_area = models.PositiveIntegerField(
        default=0, 
        verbose_name="Зарезервировання площадь (кв.м.)",
        null=True,
        blank=True,
    )
    free_booked_area = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name="Свободная площадь на складе (кв.м.)"
    )
    
    def __str__(self):
        return f"{self.client}: {self.storage} ({self.booked_area} кв.м.)"
    
    def _count_items_area(self):
        area = 0.0
        for item in self.client.items.only("area"):
            area += item.area
        return area
    
    def clean(self):
        if self.storage.free_area - self.booked_area < 0:
            raise ValidationError("На данном складе недостаточно места")
    
    def save(self, *args, **kwargs):
        self.clean()
        self.storage.free_area -= self.booked_area
        self.storage.save()
        super().save(*args, **kwargs)    
        
    def delete(self, *args, **kwargs):
        self.storage.free_area += self.storage.area
        self.storage.save()
    
    class Meta:
        verbose_name = "Склад для клиента"
        verbose_name_plural = "Склады для клиента"
    

class Project(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название*")
    client = models.ForeignKey(
        "base.Client",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Клиент",
        related_name="projects",
    )
    
    def __str__(self):
        return f"{self.name} ({self.client})"
    
    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"


class ItemCategory(models.Model):
    name = models.CharField(max_length=128, verbose_name="Название*")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"


class ItemStatus(models.Model):
    text = models.TextField(verbose_name="Текст*")
    
    def __str__(self):
        return f"{self.text}"
    
    class Meta:
        verbose_name = "Статус товаров"
        verbose_name_plural = "Статусы товаров"


class ItemImage(models.Model):
    item = models.ForeignKey(
        "base.Item",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="images",
        null=True,
        blank=True,
    )
    item_stock = models.ForeignKey(
        "base.ItemStock",
        on_delete=models.CASCADE,
        verbose_name="Приход товара",
        related_name="images",
        null=True,
        blank=True,
    )
    image = models.ImageField(
        upload_to=get_image_upload_path,
        verbose_name="Фото"
    )
    
    def clean(self):
        count = ItemImage.objects.filter(
            item=self.item,
        ).count()
        if count > 5:
            raise ValidationError(
                "Фотографий товара не может быть больше 5"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        
        if self.item_stock:
            if self.item_stock.is_approved:
                self.item = self.item_stock.item
    
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Фото для {self.item}"
        
    def image_tag(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="100" height="100" />'
            )
        return "Нет фотографии"

    image_tag.short_description = "Превью"
    
    class Meta:
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товара"


class Item(models.Model):
    article = models.CharField(max_length=6, unique=True, primary_key=True, verbose_name="Артикул")
    # TODO: is_booked
    # TODO: booking start_date
    # TODO: booking end_date
    # TODO: booking project
    # TODO: booking count
    name = models.CharField(max_length=128, verbose_name="Название*")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Масса единицы (кг)",
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True, 
        null=True, 
        verbose_name="Высота единицы (см)"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True, 
        null=True, 
        verbose_name="Ширина единицы (см)"
    )
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True, 
        null=True, 
        verbose_name="Длина единицы (см)"
    )
    count = models.PositiveIntegerField(
        verbose_name="Количество на складе*", 
        default=0
    )
    
    project = models.ForeignKey(
        "base.Project", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Проект", 
        related_name="items",
    )
    client = models.ForeignKey(
        "base.Client", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Клиент", 
        related_name="booked_items",
    )
    storage = models.ForeignKey(
        "base.Storage", 
        on_delete=models.SET_NULL,
        null=True,
        blank=False,  
        verbose_name="Склад*", 
        related_name="stored_items",
    )
    category = models.ForeignKey(
        "base.ItemCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория",
        related_name="items",
    )
    status = models.ForeignKey(
        "base.ItemStatus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="Состояние",
    )
    
    arrival_date = models.DateField(
        auto_now_add=True, 
        verbose_name="Дата прихода",
        null=True,
    )
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Срок годности (конечная дата)")
    
    def clean(self):
        pass
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.article:
            self.article = self._generate_unique_article()
        if self.project and not self.client:
            self.client = self.project.client
        super().save(*args, **kwargs)
    
    @property    
    def area(self):
        if self.width and self.length:
            return self.width * self.length
        return 0.0
    
    def _generate_unique_article(self):
        while True:
            random_number = f"{randint(0, 999999):06}"
            if not Item.objects.filter(article=random_number).exists():
                return random_number
    
    def __str__(self):
        return f"{self.name} | {self.article}"
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class ItemStock(models.Model):
    REQUEST_TYPE_CHOICES = [
        ("existing", "Заявка на существующий товар"),
        ("new", "Заявка на новый товар"),
    ]
    
    request_type = models.CharField(
        max_length=10, 
        choices=REQUEST_TYPE_CHOICES, 
        verbose_name="Тип заявки*"
    )
    existing_item = models.ForeignKey(
        Item, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="stock_requests", 
        verbose_name="Существующий товар"
    )
    count = models.PositiveIntegerField(
        verbose_name="Количество*"
    )
    planning_date = models.DateField(default=datetime.now, verbose_name="Планируемая дата*")
    date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")
    new_item_name = models.CharField(
        max_length=128, 
        blank=True, 
        null=True, 
        verbose_name="Название нового товара"
    )
    new_item_description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Описание нового товара"
    )
    new_item_weight = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Масса нового товара (кг)"
    )
    new_item_height = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Высота нового товара (см)"
    )
    new_item_width = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Ширина нового товара (см)"
    )
    new_item_length = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True, 
        null=True, 
        verbose_name="Длина нового товара (см)"
    )
    new_item_project = models.ForeignKey(
        "base.Project", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Проект нового товара", 
    )
    new_item_client = models.ForeignKey(
        "base.Client", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Клиент нового товара", 
    )
    new_item_storage = models.ForeignKey(
        "base.Storage", 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  
        verbose_name="Склад нового товара", 
    )
    new_item_category = models.ForeignKey(
        "base.ItemCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория нового товара",
    )
    new_item_status = models.ForeignKey(
        "base.ItemStatus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Состояние нового товара",
    )
    
    new_item_arrival_date = models.DateField(
        auto_now_add=True, 
        verbose_name="Дата прихода нового товара",
        null=True,
        blank=True,
    )
    new_item_expiration_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Срок годности (конечная дата) нового товара"
    )
    is_approved = models.BooleanField(
        default=False, 
        verbose_name="Подтверждение наличия на складе", 
        blank=True,
    )

    def clean(self):
        if self.request_type == 'existing' and not self.existing_item:
            raise ValidationError("Выберите существующий товар.")
        if self.request_type == "new":
            if not self.new_item_name:
                raise ValidationError("Укажите название нового товара.")
            
        
    def __str__(self):
        if self.request_type == 'existing':
            return f"Заявка на существующий товар: {self.existing_item} ({self.count})"
        return f"Заявка на новый товар: {self.new_item_name} ({self.count})"
    
    class Meta:
        verbose_name = "Заявка на приход товара"
        verbose_name_plural = "Заявки на приход товара"
        
        permissions = [
            ("can_change_sensitive_field", "Can change sensitive field")
        ]


class ItemBooking(models.Model):
    items = models.ManyToManyField(
        "base.Item", 
        verbose_name="Товар(-ы)*",
        related_name="bookings",
        through="base.ItemBookingItemM2M",
    )
    project = models.ForeignKey(
        "base.Project",
        on_delete=models.CASCADE,
        verbose_name="Проект*",
        related_name="bookings",
    )
    date = models.DateField(verbose_name="Дата", auto_now_add=True, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True, verbose_name="Город")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    start_date = models.DateField(verbose_name="Дата брони (начальная)*")
    end_date = models.DateField(verbose_name="Дата брони (конечная)*")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение брони кладовщиком")
    
    def clean(self):
        ...
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        result = ", ".join([str(item) for item in self.items.all()])
        # return f"Проект: {self.project}; Товары: {result}"
        return f"{self.project.client.name} {self.project.name} {self.start_date}-{self.end_date}"
    
    class Meta:
        verbose_name = "Заявка на бронь товаров"
        verbose_name_plural = "Заявки на бронь товаров"


class ItemBookingItemM2M(models.Model):
    item = models.ForeignKey(
        "base.Item",
        on_delete=models.CASCADE,
        related_name="booking_items",
        verbose_name="Товар*",
    )
    booking = models.ForeignKey(
        "base.ItemBooking",
        on_delete=models.CASCADE,
        related_name="item_bookings",
        verbose_name="Заявка на бронь*",
    )
    item_count = models.PositiveIntegerField(default=0, verbose_name="Количество*")
    
    def __str__(self):
        return f"{self.booking}"
    
    def clean(self):
        if self.item_count > self.item.count:
            raise ValidationError("Невозможно забронировать больше товара, чем есть на складе")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Товар на бронь"
        verbose_name_plural = "Товары на бронь"


class RecoveryImage(models.Model):
    recovery = models.ForeignKey(
        "base.ItemRecovery",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Заявка на утилизацию",
    )
    image = models.ImageField(
        upload_to=get_recovery_item_image,
        verbose_name="Фото*"
    )
    
    def clean(self):
        pass
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Фото для {self.recovery}"
        
    def image_tag(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="100" height="100" />'
            )
        return "Нет фотографии"

    image_tag.short_description = "Превью"
    
    class Meta:
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товара"


class ItemRecovery(models.Model):
    item = models.ForeignKey(
        "base.Item", 
        on_delete=models.CASCADE,
        verbose_name="Товар*",
        related_name="recoveries",
    )
    reason = models.TextField(verbose_name="Причина*")
    planning_date = models.DateField(verbose_name="Планируемая дата*")
    date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    status = models.ForeignKey(
        "base.ItemStatus",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Статус товара",
        related_name="recovered_items",
    )
    count = models.PositiveIntegerField(default=0, verbose_name="Количество")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение утилизации кладовщиком")
    is_ceo_approved = models.BooleanField(default=False, verbose_name="Утилизация разрешена руководителем")
    
    def clean(self):
        if not self.is_ceo_approved and self.is_approved:
            raise ValidationError(
                "Невозможно подтвердить утилизацию. Дождитесь разрешения руководителя"
            )
        if self.count > self.item.count:
            raise ValidationError(
                "Невозможно утилизировать больше товара, чем есть на складе"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        recovered = "Нет"
        if self.is_approved:
            recovered = "Да"
        return f"{self.item} (утилизирован: {recovered})"
    
    class Meta:
        verbose_name = "Заявка на утилизацию"
        verbose_name_plural = "Заявки на утилизацию"


class ItemRefund(models.Model):
    items = models.ManyToManyField(
        "base.Item", 
        verbose_name="Товары*",
        related_name="refunds",
        through="base.ItemRefundItemM2M",
    )
    project = models.ForeignKey(
        "base.Project",
        on_delete=models.CASCADE,
        verbose_name="Проект*",
        related_name="refunds",
    )
    status = models.ForeignKey(
        "base.ItemStatus",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Статус товара",
        related_name="refunded_items",
    )
    city = models.CharField(max_length=255, null=True, verbose_name="Город*")
    date = models.DateField(verbose_name="Дата возврата*", null=True)
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение возврата")
    
    def clean(self):
        pass
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Проект: {self.project}"
    
    class Meta:
        verbose_name = "Заявка на возвраты"
        verbose_name_plural = "Заявки на возвраты"


class ItemRefundItemM2M(models.Model):
    item = models.ForeignKey(
        "base.Item",
        on_delete=models.CASCADE,
        related_name="refund_items",
        verbose_name="Товар*",
    )
    refund = models.ForeignKey(
        "base.ItemRefund",
        on_delete=models.CASCADE,
        related_name="item_refunds",
        verbose_name="Заявка на возврат*",
    )
    
    item_count = models.PositiveIntegerField(verbose_name="Количество*")
    
    def __str__(self):
        return f"{self.refund}"
    
    class Meta:
        verbose_name = "Товар на возврат"
        verbose_name_plural = "Товары на возвраты"


class ItemConsumption(models.Model):
    """Расход товара"""
    booking = models.ForeignKey(
        "base.ItemBooking",
        on_delete=models.CASCADE,
        related_name="consumptions",
        verbose_name="Заявка на бронь*",
    )
    city = models.CharField(max_length=255, null=True, verbose_name="Город (откуда едет)*")
    
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждено складом")
    
    date = models.DateField(
        null=True,
        verbose_name="Дата отправки*"
    )
    date_created = models.DateTimeField(
        auto_now_add=True, 
        null=True,
        verbose_name="Дата создания заявки",
    )
    
    def __str__(self):
        result = ", ".join([str(item) for item in self.booking.items.all()])
        # return f"Заявка на расход {result}"
        storage = self.booking.items.first().storage
        return f"{self.booking.project.client.name} {self.booking.project.name} {self.date_created.date()} {storage}"
    
    class Meta:
        verbose_name = "Заявка на расход"
        verbose_name_plural = "Заявки на расход"