# Generated by Django 3.2 on 2021-06-18 12:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0024_auto_20210604_0758"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_es",
            field=models.TextField(blank=True, null=True),
        ),
    ]
