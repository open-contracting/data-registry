# Generated by Django 3.2.4 on 2021-08-27 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_registry', '0031_auto_20210820_2014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='frozen',
            field=models.BooleanField(default=False, help_text='If the spider is broken, check this box to prevent the scheduling of new jobs.'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='public',
            field=models.BooleanField(default=False, help_text="If the active job's tasks completed without errors and all the fields below in all languages are filled in, check this box to make the publication visible to anonymous users. Otherwise, it is visible to administrators only."),
        ),
        migrations.AlterField(
            model_name='job',
            name='active',
            field=models.BooleanField(default=False, help_text="Set this as the active job for the publication from the publication's page."),
        ),
        migrations.AlterField(
            model_name='job',
            name='context',
            field=models.JSONField(blank=True, help_text='<dl><dt><code>spider</code></dt><dd>The name of the spider in Kingfisher Collect</dd><dt><code>job_id</code></dt><dd>The ID of the job in Scrapyd</dd><dt><code>scrapy_log</code></dt><dd>A local URL to the log file of the crawl in Scrapyd</dd><dt><code>process_id</code></dt><dd>The ID of the base collection in Kingfisher Process</dd><dt><code>process_id_pelican</code></dt><dd>The ID of the compiled collection in Kingfisher Process</dd><dt><code>process_data_version</code></dt><dd>The data version of the collection in Kingfisher Process</dd><dt><code>pelican_id</code></dt><dd>The ID of the dataset in Pelican</dd><dt><code>pelican_dataset_name</code></dt><dd>The name of the dataset in Pelican</dd></dl>', null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='keep_all_data',
            field=models.BooleanField(default=False, help_text='By default, temporary data created by job tasks is deleted after the job is completed. Only the data registry\'s models\' data and JSON exports are retained. To preserve temporary data for debugging, check this box. Then, when ready, uncheck this box and run the "cbom" management command.', verbose_name='preserve temporary data'),
        ),
    ]