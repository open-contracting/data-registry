# Generated by Django 3.1.6 on 2021-03-29 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_registry", "0002_auto_20210329_0951"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="amendments_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="awards_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="contracts_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="documents_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="milestones_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="parties_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="plannings_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="collection",
            name="tenders_count",
            field=models.IntegerField(default=0),
        ),
    ]
