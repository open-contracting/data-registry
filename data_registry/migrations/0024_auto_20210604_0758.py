# Generated by Django 3.2 on 2021-06-04 07:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0023_collection_country_flag"),
    ]

    operations = [
        migrations.AlterField(
            model_name="license",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="license",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="license",
            name="description_es",
            field=models.TextField(blank=True, null=True),
        ),
    ]
