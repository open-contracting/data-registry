# Generated by Django 3.2 on 2021-08-04 09:41

from django.db import migrations, models


def move_values(apps, schema_editor):
    Job = apps.get_model("data_registry", "Job")
    jobs = Job.objects.all()

    for job in jobs:
        job.tenders_count = job.collection.tenders_count
        job.tenderers_count = job.collection.tenderers_count
        job.tenders_items_count = job.collection.tenders_items_count
        job.parties_count = job.collection.parties_count
        job.awards_count = job.collection.awards_count
        job.awards_items_count = job.collection.awards_items_count
        job.awards_suppliers_count = job.collection.awards_suppliers_count
        job.contracts_count = job.collection.contracts_count
        job.contracts_items_count = job.collection.contracts_items_count
        job.contracts_transactions_count = job.collection.contracts_transactions_count
        job.documents_count = job.collection.documents_count
        job.plannings_count = job.collection.plannings_count
        job.milestones_count = job.collection.milestones_count
        job.amendments_count = job.collection.amendments_count
        job.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0027_auto_20210804_0854'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='amendments_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='awards_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='awards_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='awards_suppliers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='contracts_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='contracts_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='contracts_transactions_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='date_from',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='date_to',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='documents_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='license',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='milestones_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='ocid_prefix',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='parties_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='plannings_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='tenderers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='tenders_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='tenders_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(move_values),
    ]