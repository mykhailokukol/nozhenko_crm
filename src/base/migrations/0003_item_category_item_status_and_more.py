# Generated by Django 4.0.4 on 2024-08-20 14:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_storageclientm2m_options_storage_free_area_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='base.itemcategory', verbose_name='Категория'),
        ),
        migrations.AddField(
            model_name='item',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='base.itemstatus', verbose_name='Состояние'),
        ),
        migrations.AlterField(
            model_name='storageclientm2m',
            name='booked_area',
            field=models.PositiveIntegerField(default=0, verbose_name='Зарезервировання площадь (кв.м.)'),
        ),
    ]
