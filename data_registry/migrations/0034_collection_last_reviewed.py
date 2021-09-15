# Generated by Django 3.2.4 on 2021-09-15 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0033_collection_source_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='last_reviewed',
            field=models.DateField(blank=True, help_text='The date on which the quality summary was last confirmed to be correct. Only the year and month are published.', null=True, verbose_name='last reviewed'),
        ),
    ]
