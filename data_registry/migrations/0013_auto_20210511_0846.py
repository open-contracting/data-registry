# Generated by Django 3.2 on 2021-05-11 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0012_job_context'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='description_long',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='frozen',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='collection',
            name='public',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='job',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
