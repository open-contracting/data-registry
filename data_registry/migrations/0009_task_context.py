# Generated by Django 3.2 on 2021-05-06 12:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0008_auto_20210506_1207"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="context",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
