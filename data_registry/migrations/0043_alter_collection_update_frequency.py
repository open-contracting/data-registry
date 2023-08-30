# Generated by Django 4.2.3 on 2023-08-30 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0042_alter_collection_update_frequency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='update_frequency',
            field=models.TextField(blank=True, choices=[('UNKNOWN', 'Unknown'), ('REAL_TIME', 'Real time'), ('HOURLY', 'Hourly'), ('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('QUARTERLY', 'Every 3 months'), ('HALF_YEARLY', 'Every 6 months'), ('ANNUALLY', 'Annually')], default='UNKNOWN', help_text='The frequency at which the source updates the publication.'),
        ),
    ]
