# Generated by Django 4.2.16 on 2024-11-07 04:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0055_alter_collection_active_job"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="publication_policy",
            field=models.TextField(blank=True),
        ),
    ]