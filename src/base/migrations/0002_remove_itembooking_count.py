# Generated by Django 5.1 on 2024-09-13 13:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itembooking',
            name='count',
        ),
    ]
