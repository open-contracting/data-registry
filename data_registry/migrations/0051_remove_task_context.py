# Generated by Django 4.2.15 on 2024-11-04 23:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0050_collection_active_job"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="context",
        ),
    ]
