from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base.models import ItemStock


def create_custom_permissions():
    ct = ContentType.objects.get_for_model(ItemStock)
    if not Permission.objects.filter(codename="can_approve_stock").exists():
        Permission.objects.create(
            codename="can_approve_stock",
            name="Может подтверждать наличие товара",
            content_type=ct,
        )