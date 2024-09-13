from random import randint

from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser


def get_image_upload_path(instance, filename):
    return f"items/{instance.item.article}/{filename}"


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
        verbose_name="Товар*",
        related_name="images",
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
    count = models.PositiveIntegerField(verbose_name="Количество*", default=0)
    
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
        verbose_name="Дата прихода*",
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
        return f"{self.article} | {self.name}"
    
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
    count = models.PositiveIntegerField(
        verbose_name="Количество*"
    )
    is_approved = models.BooleanField(
        default=False, 
        verbose_name="Подтверждение наличия", 
        blank=True,
    )

    def clean(self):
        if self.request_type == 'existing' and not self.existing_item:
            raise ValidationError("Выберите существующий товар.")
        if self.request_type == 'new' and not self.new_item_name:
            raise ValidationError("Укажите название нового товара.")
        if self.request_type == 'new' and not self.new_item_description:
            raise ValidationError("Укажите описание нового товара.")
        
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
    item = models.ForeignKey(
        "base.Item", 
        on_delete=models.CASCADE,
        verbose_name="Товар*",
        related_name="bookings",
    )
    count = models.PositiveIntegerField(verbose_name="Количество*")
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
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение брони")
    
    def clean(self):
        if not self.item.is_approved:
            raise ValidationError("Невозможно забронировать товар, пока не подтверждено наличие на складе")
        if self.count > self.item.count:
            raise ValidationError("Невозможно забронировать большее количество товара, чем есть на складе")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    # def delete(self, *args, **kwargs):
    #     item = Item.objects.get(id=self.item.id)
    #     item.is_booked = False
    #     item.project = None
    #     item.save()
    #     super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item} на {self.project}"
    
    class Meta:
        verbose_name = "Запрос на бронь товаров"
        verbose_name_plural = "Запросы на бронь товаров"


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
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение утилизации")
    is_ceo_approved = models.BooleanField(default=False, verbose_name="Утилизация разрешена руководителем")
    
    def clean(self):
        if not self.is_ceo_approved and self.is_approved:
            raise ValidationError(
                "Невозможно подтвердить утилизацию. Дождитесь разрешения руководителя"
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
        verbose_name = "Запрос на утилизацию"
        verbose_name_plural = "Запросы на утилизацию"


class ItemRefund(models.Model):
    item = models.ForeignKey(
        "base.Item", 
        on_delete=models.CASCADE,
        verbose_name="Товар*",
        related_name="refunds",
    )
    count = models.PositiveIntegerField(verbose_name="Количество*")
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
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение возврата")
    
    def clean(self):
        if self.count > 0:
            bookings = ItemBooking.objects.filter(
                item=self.item,
                is_approved=True,
            ).only("count", "project")
            for booking in bookings:
                if self.count > booking.count:
                    raise ValidationError(
                        f"Невозможно запросить возврат на большее количество, чем было забронировано для проекта {booking.project}"
                    )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item} с проекта {self.project}"
    
    class Meta:
        verbose_name = "Запрос на возвраты"
        verbose_name_plural = "Запросы на возвраты"