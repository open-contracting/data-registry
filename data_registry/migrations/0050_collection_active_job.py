# Generated by Django 4.2.15 on 2024-11-04 22:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0049_alter_collection_license_custom_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="active_job",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="+",
                to="data_registry.job",
                verbose_name="active job",
                help_text="A job is a set of tasks to collect and process data from a publication. A job can be selected once it is completed. If a new job completes, it becomes the active job.",
            ),
        ),
        migrations.RunSQL(
            """
            UPDATE data_registry_collection c
            SET active_job_id = j.id
            FROM data_registry_job j
            WHERE
                j.collection_id = c.id
                AND active = TRUE
            """
        ),
    ]