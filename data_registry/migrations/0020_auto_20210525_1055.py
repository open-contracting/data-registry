# Generated by Django 3.2 on 2021-05-25 10:55

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0019_auto_20210513_0527'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='awards_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='collection',
            name='awards_suppliers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='collection',
            name='contracts_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='collection',
            name='contracts_transactions_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='collection',
            name='tenderers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='collection',
            name='tenders_items_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='collection',
            name='additional_data',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='additional_data_en',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='additional_data_es',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description_long',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description_long_en',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description_long_es',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='summary',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='summary_en',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='summary_es',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='issue',
            name='description',
            field=markdownx.models.MarkdownxField(),
        ),
        migrations.AlterField(
            model_name='issue',
            name='description_en',
            field=markdownx.models.MarkdownxField(null=True),
        ),
        migrations.AlterField(
            model_name='issue',
            name='description_es',
            field=markdownx.models.MarkdownxField(null=True),
        ),
    ]