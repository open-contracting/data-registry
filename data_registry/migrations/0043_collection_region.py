# Generated by Django 4.2.3 on 2023-11-02 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0042_alter_collection_update_frequency'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='region',
            field=models.TextField(blank=True, choices=[('MEA', 'Africa and Middle East'), ('AS', 'Asia'), ('EECA', 'Eastern Europe & Central Asia'), ('EU', 'Europe'), ('LAC', 'Latin America & Caribbean'), ('NA', 'North America'), ('OC', 'Oceania')], help_text='The name of the region to which the country belongs.'),
        ),
    ]