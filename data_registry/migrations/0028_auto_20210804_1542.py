# Generated by Django 3.2 on 2021-08-04 09:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0029_merge_0028_auto_20210804_0941_0028_auto_20210804_0951"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="collection",
            name="amendments_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="awards_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="awards_items_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="awards_suppliers_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="contracts_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="contracts_items_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="contracts_transactions_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="date_from",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="date_to",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="documents_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="license",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="milestones_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="ocid_prefix",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="parties_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="plannings_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="tenderers_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="tenders_count",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="tenders_items_count",
        ),
    ]
