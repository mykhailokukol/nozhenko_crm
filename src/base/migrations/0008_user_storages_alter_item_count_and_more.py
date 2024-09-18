# Generated by Django 5.1 on 2024-09-15 13:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_itemstock_new_item_arrival_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='storages',
            field=models.ManyToManyField(blank=True, related_name='users', to='base.storage', verbose_name='Склады'),
        ),
        migrations.AlterField(
            model_name='item',
            name='count',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество на складе*'),
        ),
        migrations.AlterField(
            model_name='itembooking',
            name='is_approved',
            field=models.BooleanField(default=False, verbose_name='Подтверждение брони кладовщиком'),
        ),
        migrations.AlterField(
            model_name='itemconsumption',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='itemrecovery',
            name='is_approved',
            field=models.BooleanField(default=False, verbose_name='Подтверждение утилизации кладовщиком'),
        ),
        migrations.AlterField(
            model_name='itemstock',
            name='new_item_storage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.storage', verbose_name='Склад нового товара'),
        ),
    ]
