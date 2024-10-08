# Generated by Django 3.2.4 on 2021-08-27 21:24

from django.db import migrations


def set_null_values_to_empty_strings(apps, schema_editor):
    models = {
        "Collection": [
            "additional_data",
            "description_long",
            "language",
            "summary",
            # The below changes correspond to the addition of `fallback_undefined = ""`
            "additional_data_en",
            "additional_data_es",
            "additional_data_ru",
            "country_en",
            "country_es",
            "country_ru",
            "description_en",
            "description_es",
            "description_ru",
            "description_long_en",
            "description_long_es",
            "description_long_ru",
            "language_en",
            "language_es",
            "language_ru",
            "summary_en",
            "summary_es",
            "summary_ru",
            "title_en",
            "title_es",
            "title_ru",
        ],
        "Job": [
            "license",
            "ocid_prefix",
            "status",
        ],
        "Task": [
            "note",
            "result",
            "status",
            "type",
        ],
    }

    for model_name, fields in models.items():
        model = apps.get_model("data_registry", model_name)
        for instance in model.objects.all():
            for field in fields:
                if getattr(instance, field) is None:
                    setattr(instance, field, "")
            instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0030_alter_fields"),
    ]

    operations = [
        migrations.RunPython(set_null_values_to_empty_strings),
    ]
