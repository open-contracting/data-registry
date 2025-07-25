# Generated by Django 4.2.22 on 2025-07-04 20:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0065_job_coverage_alter_task_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="status",
            field=models.TextField(
                blank=True,
                choices=[("PLANNED", "PLANNED"), ("RUNNING", "RUNNING"), ("COMPLETED", "COMPLETED")],
                default="PLANNED",
            ),
        ),
    ]
