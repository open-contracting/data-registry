# Generated by Django 3.2.4 on 2021-08-20 20:14

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0032_auto_20210827_2124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='additional_data',
            field=markdownx.models.MarkdownxField(blank=True, default='', help_text='Any notable highlights about the available data, such as extensions used or additional fields, as Markdown text.', verbose_name='data availability'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='description_long',
            field=markdownx.models.MarkdownxField(blank=True, default='', help_text='The remaining paragraphs of the description of the publication, as Markdown text, which will appear under "Show more".'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='language',
            field=models.CharField(blank=True, default='', help_text='The languages used within data fields: for example, "Spanish".', max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='summary',
            field=markdownx.models.MarkdownxField(blank=True, default='', help_text='A short summary of quality issues, as Markdown text. Individual issues can be described below, which will be rendered as a bullet list.', verbose_name='quality summary'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='job',
            name='license',
            field=models.CharField(blank=True, default='', max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='job',
            name='ocid_prefix',
            field=models.CharField(blank=True, default='', max_length=2048, verbose_name='OCID prefix'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(blank=True, choices=[('WAITING', 'WAITING'), ('PLANNED', 'PLANNED'), ('RUNNING', 'RUNNING'), ('COMPLETED', 'COMPLETED')], default='', max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='task',
            name='note',
            field=models.TextField(blank=True, default='', help_text='Metadata about any failure.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='task',
            name='result',
            field=models.CharField(blank=True, choices=[('OK', 'OK'), ('FAILED', 'FAILED')], default='', max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(blank=True, choices=[('WAITING', 'WAITING'), ('PLANNED', 'PLANNED'), ('RUNNING', 'RUNNING'), ('COMPLETED', 'COMPLETED')], default='', max_length=2048),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(blank=True, default='', max_length=2048),
            preserve_default=False,
        ),
    ]