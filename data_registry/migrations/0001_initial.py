# Generated by Django 3.1.6 on 2021-03-16 15:14

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.TextField()),
                ("ocds_label", models.TextField()),
                ("country", models.TextField()),
            ],
        ),
    ]
