# Generated by Django 3.2.4 on 2021-08-13 19:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0029_auto_20210813_1929"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="additional_data",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Any notable highlights about the available data, such as extensions used or additional fields, as Markdown text.",
                null=True,
                verbose_name="data availability",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="additional_data_en",
            field=models.TextField(
                blank=True,
                help_text="Any notable highlights about the available data, such as extensions used or additional fields, as Markdown text.",
                null=True,
                verbose_name="data availability",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="additional_data_es",
            field=models.TextField(
                blank=True,
                help_text="Any notable highlights about the available data, such as extensions used or additional fields, as Markdown text.",
                null=True,
                verbose_name="data availability",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="additional_data_ru",
            field=models.TextField(
                blank=True,
                help_text="Any notable highlights about the available data, such as extensions used or additional fields, as Markdown text.",
                null=True,
                verbose_name="data availability",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="country",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The official name of the country from which the data originates.",
                max_length=2048,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="country_en",
            field=models.CharField(
                blank=True,
                help_text="The official name of the country from which the data originates.",
                max_length=2048,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="country_es",
            field=models.CharField(
                blank=True,
                help_text="The official name of the country from which the data originates.",
                max_length=2048,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="country_flag",
            field=models.CharField(blank=True, default="", max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="country_ru",
            field=models.CharField(
                blank=True,
                help_text="The official name of the country from which the data originates.",
                max_length=2048,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text='The first paragraph of the description of the publication, as Markdown text, following the <a href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#heading=h.fksp8fxgoi7v">template and guidance</a>.',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_en",
            field=models.TextField(
                blank=True,
                help_text='The first paragraph of the description of the publication, as Markdown text, following the <a href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#heading=h.fksp8fxgoi7v">template and guidance</a>.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_es",
            field=models.TextField(
                blank=True,
                help_text='The first paragraph of the description of the publication, as Markdown text, following the <a href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#heading=h.fksp8fxgoi7v">template and guidance</a>.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_long",
            field=models.TextField(
                blank=True,
                default="",
                help_text='The remaining paragraphs of the description of the publication, as Markdown text, which will appear under "Show more".',
                null=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_long_en",
            field=models.TextField(
                blank=True,
                help_text='The remaining paragraphs of the description of the publication, as Markdown text, which will appear under "Show more".',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_long_es",
            field=models.TextField(
                blank=True,
                help_text='The remaining paragraphs of the description of the publication, as Markdown text, which will appear under "Show more".',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_long_ru",
            field=models.TextField(
                blank=True,
                help_text='The remaining paragraphs of the description of the publication, as Markdown text, which will appear under "Show more".',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description_ru",
            field=models.TextField(
                blank=True,
                help_text='The first paragraph of the description of the publication, as Markdown text, following the <a href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#heading=h.fksp8fxgoi7v">template and guidance</a>.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="frozen",
            field=models.BooleanField(
                default=False, help_text="If the spider is broken, check this box to prevent new jobs from running."
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="language",
            field=models.CharField(
                blank=True,
                default="",
                help_text='The languages used within data fields: for example, "Spanish".',
                max_length=2048,
                null=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="last_update",
            field=models.DateField(
                blank=True,
                help_text="The date on which the most recent 'collect' job task completed.",
                null=True,
                verbose_name="last updated",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="license_custom",
            field=models.ForeignKey(
                blank=True,
                help_text="If not set, the Overview section will display the license URL within the OCDS package.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="collection",
                to="data_registry.license",
                verbose_name="data license",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="public",
            field=models.BooleanField(
                default=False,
                help_text="If the active job's tasks completed without errors and all fields below in all languages are filled in, check this box.",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="source_id",
            field=models.CharField(
                help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, Kingfisher Collect needs to be re-deployed to the registry's server.",
                max_length=2048,
                verbose_name="source ID",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="summary",
            field=models.TextField(
                blank=True,
                default="",
                help_text="A short summary of quality issues, as Markdown text. Individual issues can be described below, which will be rendered as a bullet list.",
                verbose_name="quality summary",
                null=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="collection",
            name="summary_en",
            field=models.TextField(
                blank=True,
                help_text="A short summary of quality issues, as Markdown text. Individual issues can be described below, which will be rendered as a bullet list.",
                null=True,
                verbose_name="quality summary",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="summary_es",
            field=models.TextField(
                blank=True,
                help_text="A short summary of quality issues, as Markdown text. Individual issues can be described below, which will be rendered as a bullet list.",
                null=True,
                verbose_name="quality summary",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="summary_ru",
            field=models.TextField(
                blank=True,
                help_text="A short summary of quality issues, as Markdown text. Individual issues can be described below, which will be rendered as a bullet list.",
                null=True,
                verbose_name="quality summary",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="title",
            field=models.TextField(
                help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, and omitting the country name.'
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="title_en",
            field=models.TextField(
                help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, and omitting the country name.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="title_es",
            field=models.TextField(
                help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, and omitting the country name.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="title_ru",
            field=models.TextField(
                help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, and omitting the country name.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="update_frequency",
            field=models.CharField(
                blank=True,
                choices=[("MONTHLY", "MONTHLY"), ("HALF_YEARLY", "HALF_YEARLY"), ("ANNUALLY", "ANNUALLY")],
                default="",
                help_text="The frequency at which the registry updates the publication, based on the frequency at which the publication is updated.",
                max_length=2048,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="issue",
            name="description",
            field=models.TextField(help_text="A one-line description of the quality issue, as Markdown text."),
        ),
        migrations.AlterField(
            model_name="issue",
            name="description_en",
            field=models.TextField(
                help_text="A one-line description of the quality issue, as Markdown text.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="description_es",
            field=models.TextField(
                help_text="A one-line description of the quality issue, as Markdown text.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="description_ru",
            field=models.TextField(
                help_text="A one-line description of the quality issue, as Markdown text.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="active",
            field=models.BooleanField(
                default=False, help_text="Set this as the active job for the collection from the collection's page."
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="archived",
            field=models.BooleanField(
                default=False,
                help_text="Whether the temporary data created by job tasks has been deleted.",
                verbose_name="temporary data deleted",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="job",
                to="data_registry.collection",
                verbose_name="publication",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="context",
            field=models.JSONField(
                blank=True,
                help_text="Refer to the User Guide to interpret and use this information for debugging.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="date_from",
            field=models.DateField(blank=True, null=True, verbose_name="minimum release date"),
        ),
        migrations.AlterField(
            model_name="job",
            name="date_to",
            field=models.DateField(blank=True, null=True, verbose_name="maximum release date"),
        ),
        migrations.AlterField(
            model_name="job",
            name="end",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="job ended at"),
        ),
        migrations.AlterField(
            model_name="job",
            name="keep_all_data",
            field=models.BooleanField(
                default=False,
                help_text='By default, temporary data created by job tasks is deleted after the job is completed. To preserve this data for debugging, check this box. Then, when ready, uncheck this box and run the "cbom" management command.',
                verbose_name="preserve temporary data",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="ocid_prefix",
            field=models.CharField(blank=True, max_length=2048, null=True, verbose_name="OCID prefix"),
        ),
        migrations.AlterField(
            model_name="job",
            name="start",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="job started at"),
        ),
        migrations.AlterField(
            model_name="license",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="A brief description of the permissions, conditions and limitations, as Markdown text.",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="license",
            name="description_en",
            field=models.TextField(
                blank=True,
                help_text="A brief description of the permissions, conditions and limitations, as Markdown text.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="description_es",
            field=models.TextField(
                blank=True,
                help_text="A brief description of the permissions, conditions and limitations, as Markdown text.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="description_ru",
            field=models.TextField(
                blank=True,
                help_text="A brief description of the permissions, conditions and limitations, as Markdown text.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="name",
            field=models.CharField(
                blank=True, default="", help_text="The official name of the license.", max_length=2048
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="license",
            name="name_en",
            field=models.CharField(
                blank=True, help_text="The official name of the license.", max_length=2048, null=True
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="name_es",
            field=models.CharField(
                blank=True, help_text="The official name of the license.", max_length=2048, null=True
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="name_ru",
            field=models.CharField(
                blank=True, help_text="The official name of the license.", max_length=2048, null=True
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="url",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The canonical URL of the license.",
                max_length=2048,
                verbose_name="URL",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="task",
            name="note",
            field=models.TextField(blank=True, help_text="Metadata about any failure.", null=True),
        ),
    ]
