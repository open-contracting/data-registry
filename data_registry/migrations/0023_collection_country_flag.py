# Generated by Django 3.2 on 2021-06-04 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0022_auto_20210603_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='country_flag',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
