# Generated by Django 3.2.15 on 2022-09-23 02:59

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0037_alter_collection_last_update"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="collection",
            name="csv_format",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="excel_format",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="json_format",
        ),
    ]
