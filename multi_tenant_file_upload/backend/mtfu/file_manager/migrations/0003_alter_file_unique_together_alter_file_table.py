# Generated by Django 4.2.1 on 2023-05-11 15:08

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("file_manager", "0002_file_delete_flg"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="file",
            unique_together={("tenant", "name", "resource", "resource_id")},
        ),
        migrations.AlterModelTable(
            name="file",
            table="file",
        ),
    ]
