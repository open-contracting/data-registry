# Generated by Django 3.2 on 2021-05-13 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0018_auto_20210513_0524'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='additional_data_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='additional_data_es',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='summary_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='summary_es',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='license',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='license',
            name='description_es',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='license',
            name='name_en',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name='license',
            name='name_es',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
