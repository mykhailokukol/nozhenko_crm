# Generated by Django 5.1 on 2024-09-25 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0017_itemrefundimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemrefund',
            name='city',
            field=models.CharField(max_length=255, null=True, verbose_name='Город (откуда едет)*'),
        ),
    ]
