# Generated by Django 4.2.3 on 2023-08-30 21:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0043_alter_collection_update_frequency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="type",
            field=models.TextField(
                blank=True,
                choices=[
                    ("collect", "Collect"),
                    ("process", "Process"),
                    ("pelican", "Pelican"),
                    ("exporter", "Exporter"),
                    ("flattener", "Flattener"),
                ],
            ),
        ),
    ]
