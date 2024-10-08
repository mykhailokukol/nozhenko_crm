# Generated by Django 5.1 on 2024-09-26 17:54

import base.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0018_alter_itemrefund_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemconsumption',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание'),
        ),
        migrations.CreateModel(
            name='ItemConsumptionImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=base.models.get_consumption_item_image_path, verbose_name='Фото*')),
                ('consumption', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='base.itemconsumption', verbose_name='Заявка на расход')),
            ],
            options={
                'verbose_name': 'Фотография товаров',
                'verbose_name_plural': 'Фотографии товаров',
            },
        ),
    ]
