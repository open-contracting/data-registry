# Generated by Django 3.2.16 on 2023-06-15 19:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0039_update_collection_country_flag_value'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collection',
            old_name='update_frequency',
            new_name='retrieval_frequency',
        ),
    ]
