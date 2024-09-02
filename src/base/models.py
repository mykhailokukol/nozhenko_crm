from random import randint

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser


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
    
    username = models.CharField(max_length=128, verbose_name="Никнейм", unique=True)
    password = models.CharField(max_length=255, verbose_name="Пароль")
    
    first_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="Отчество")
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Менеджер?",
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Руководитель/Администратор?",
    )
    
    date_joined = models.DateField(auto_now_add=True)
    
    client = models.ForeignKey(
        "base.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Клиент",
        related_name="users",
    )
    
    def __str__(self) -> str:
        return f"{self.username}"
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(models.Model):
    name = models.CharField(max_length=128, verbose_name="Имя/Название")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Storage(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название")
    area = models.PositiveIntegerField(
        verbose_name="Площадь (кв.м.)",
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
        verbose_name="Склад",
    )
    client = models.ForeignKey(
        "base.Client", 
        on_delete=models.CASCADE,
        verbose_name="Клиент",
    )
    booked_area = models.PositiveIntegerField(
        default=0, 
        verbose_name="Зарезервировання площадь (кв.м.)"
    )
    
    def __str__(self):
        return f"{self.client}: {self.storage} ({self.booked_area} кв.м.)"
    
    def clean(self):
        if self.storage.free_area - self.booked_area < 0:
            raise ValidationError("На данном складе недостаточно места")
    
    def save(self, *args, **kwargs):
        self.clean()
        self.storage.free_area -= self.booked_area
        self.storage.save()
        super().save(*args, **kwargs)    
        
    def delete(self, *args, **kwargs):
        self.storage.free_area = self.storage.area
        self.storage.save()
    
    class Meta:
        verbose_name = "Склад для клиента"
        verbose_name_plural = "Склады для клиента"
    

class Project(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название")
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
    name = models.CharField(max_length=128, verbose_name="Название")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"


class ItemStatus(models.Model):
    text = models.TextField(verbose_name="Текст")
    
    def __str__(self):
        return f"{self.text}"
    
    class Meta:
        verbose_name = "Статус товаров"
        verbose_name_plural = "Статусы товаров"


class Item(models.Model):
    article = models.CharField(max_length=6, unique=True, primary_key=True, verbose_name="Артикул")
    name = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    
    weight = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Масса (кг)")
    height = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Высота (см)")
    width = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Ширина (см)")
    length = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Длина (см)")
    count = models.PositiveIntegerField(verbose_name="Количество")
    
    is_booked = models.BooleanField(default=False, verbose_name="Забронирован?")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждение наличия")
    
    project = models.ForeignKey(
        "base.Project", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Проект", 
        related_name="items"
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
    
    arrival_date = models.DateField(auto_now_add=True, verbose_name="Дата прихода")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Срок годности (конечная дата)")
    
    def save(self, *args, **kwargs):
        if not self.article:
            self.article = self._generate_unique_article()
        super().save(*args, **kwargs)
    
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