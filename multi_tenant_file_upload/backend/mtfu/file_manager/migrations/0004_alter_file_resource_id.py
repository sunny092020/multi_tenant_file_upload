# Generated by Django 4.2.1 on 2023-05-13 01:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("file_manager", "0003_alter_file_unique_together_alter_file_table"),
    ]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="resource_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]