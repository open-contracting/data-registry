# Generated by Django 3.2.8 on 2021-11-15 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0034_collection_last_reviewed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='country',
            field=models.TextField(blank=True, help_text='The official name of the country from which the data originates.'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='country_en',
            field=models.TextField(blank=True, help_text='The official name of the country from which the data originates.', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='country_es',
            field=models.TextField(blank=True, help_text='The official name of the country from which the data originates.', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='country_flag',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='country_ru',
            field=models.TextField(blank=True, help_text='The official name of the country from which the data originates.', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='language',
            field=models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='language_en',
            field=models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='language_es',
            field=models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='language_ru',
            field=models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='source_id',
            field=models.TextField(help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, Kingfisher Collect needs to be re-deployed to the registry's server.", verbose_name='source ID'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='update_frequency',
            field=models.TextField(blank=True, choices=[('MONTHLY', 'MONTHLY'), ('HALF_YEARLY', 'HALF_YEARLY'), ('ANNUALLY', 'ANNUALLY')], help_text='The frequency at which the registry updates the publication, based on the frequency at which the publication is updated.'),
        ),
        migrations.AlterField(
            model_name='job',
            name='context',
            field=models.JSONField(blank=True, default=dict, help_text='<dl><dt><code>spider</code></dt><dd>The name of the spider in Kingfisher Collect</dd><dt><code>job_id</code></dt><dd>The ID of the job in Scrapyd</dd><dt><code>scrapy_log</code></dt><dd>A local URL to the log file of the crawl in Scrapyd</dd><dt><code>process_id</code></dt><dd>The ID of the base collection in Kingfisher Process</dd><dt><code>process_id_pelican</code></dt><dd>The ID of the compiled collection in Kingfisher Process</dd><dt><code>process_data_version</code></dt><dd>The data version of the collection in Kingfisher Process</dd><dt><code>pelican_id</code></dt><dd>The ID of the dataset in Pelican</dd><dt><code>pelican_dataset_name</code></dt><dd>The name of the dataset in Pelican</dd></dl>'),
        ),
        migrations.AlterField(
            model_name='job',
            name='keep_all_data',
            field=models.BooleanField(default=False, help_text='By default, temporary data created by job tasks is deleted after the job is completed. Only the data registry\'s models\' data and JSON exports are retained. To preserve temporary data for debugging, check this box. Then, when ready, uncheck this box and run the "manageprocess" management command.', verbose_name='preserve temporary data'),
        ),
        migrations.AlterField(
            model_name='job',
            name='license',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='ocid_prefix',
            field=models.TextField(blank=True, verbose_name='OCID prefix'),
        ),
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.TextField(blank=True, choices=[('WAITING', 'WAITING'), ('PLANNED', 'PLANNED'), ('RUNNING', 'RUNNING'), ('COMPLETED', 'COMPLETED')]),
        ),
        migrations.AlterField(
            model_name='license',
            name='name',
            field=models.TextField(blank=True, help_text='The official name of the license.'),
        ),
        migrations.AlterField(
            model_name='license',
            name='name_en',
            field=models.TextField(blank=True, help_text='The official name of the license.', null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='name_es',
            field=models.TextField(blank=True, help_text='The official name of the license.', null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='name_ru',
            field=models.TextField(blank=True, help_text='The official name of the license.', null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='url',
            field=models.TextField(blank=True, help_text='The canonical URL of the license.', verbose_name='URL'),
        ),
        migrations.AlterField(
            model_name='task',
            name='context',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='task',
            name='result',
            field=models.TextField(blank=True, choices=[('OK', 'OK'), ('FAILED', 'FAILED')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.TextField(blank=True, choices=[('WAITING', 'WAITING'), ('PLANNED', 'PLANNED'), ('RUNNING', 'RUNNING'), ('COMPLETED', 'COMPLETED')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.TextField(blank=True),
        ),
    ]