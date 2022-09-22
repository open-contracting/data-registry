from django.db import models
from django.utils.translation import gettext_lazy as _
from markdownx.models import MarkdownxField


class Job(models.Model):
    collection = models.ForeignKey(
        "Collection", related_name="job", on_delete=models.CASCADE, verbose_name="publication"
    )
    start = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="job started at")
    end = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="job ended at")

    class Status(models.TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = models.TextField(choices=Status.choices, blank=True)

    context = models.JSONField(
        blank=True,
        default=dict,
        help_text="<dl>"
        "<dt><code>spider</code></dt>"
        "<dd>The name of the spider in Kingfisher Collect</dd>"
        "<dt><code>job_id</code></dt>"
        "<dd>The ID of the job in Scrapyd</dd>"
        "<dt><code>scrapy_log</code></dt>"
        "<dd>A local URL to the log file of the crawl in Scrapyd</dd>"
        "<dt><code>process_id</code></dt>"
        "<dd>The ID of the base collection in Kingfisher Process</dd>"
        "<dt><code>process_id_pelican</code></dt>"
        "<dd>The ID of the compiled collection in Kingfisher Process</dd>"
        "<dt><code>process_data_version</code></dt>"
        "<dd>The data version of the collection in Kingfisher Process</dd>"
        "<dt><code>pelican_id</code></dt>"
        "<dd>The ID of the dataset in Pelican</dd>"
        "<dt><code>pelican_dataset_name</code></dt>"
        "<dd>The name of the dataset in Pelican</dd>"
        "</dl>",
    )

    active = models.BooleanField(
        default=False, help_text="Set this as the active job for the publication from the publication's page."
    )

    archived = models.BooleanField(
        default=False,
        verbose_name="temporary data deleted",
        help_text="Whether the temporary data created by job tasks has been deleted.",
    )

    keep_all_data = models.BooleanField(
        default=False,
        verbose_name="preserve temporary data",
        help_text="By default, temporary data created by job tasks is deleted after the job "
        "is completed. Only the data registry's models' data and JSON exports are "
        "retained. To preserve temporary data for debugging, check this box. Then, "
        'when ready, uncheck this box and run the "manageprocess" management command.',
    )

    tenders_count = models.IntegerField(default=0)
    tenderers_count = models.IntegerField(default=0)
    tenders_items_count = models.IntegerField(default=0)
    parties_count = models.IntegerField(default=0)
    awards_count = models.IntegerField(default=0)
    awards_items_count = models.IntegerField(default=0)
    awards_suppliers_count = models.IntegerField(default=0)
    contracts_count = models.IntegerField(default=0)
    contracts_items_count = models.IntegerField(default=0)
    contracts_transactions_count = models.IntegerField(default=0)
    documents_count = models.IntegerField(default=0)
    plannings_count = models.IntegerField(default=0)
    milestones_count = models.IntegerField(default=0)
    amendments_count = models.IntegerField(default=0)

    date_from = models.DateField(blank=True, null=True, verbose_name="minimum release date")
    date_to = models.DateField(blank=True, null=True, verbose_name="maximum release date")
    ocid_prefix = models.TextField(blank=True, verbose_name="OCID prefix")
    license = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.format_datetime(self.start)} .. {self.format_datetime(self.end)} ({self.id})"

    def format_datetime(self, dt):
        return dt.strftime("%d-%b-%y") if dt else ""

    def get_max_number_of_rows(self):
        count_columns = filter(lambda name: "_count" in name, dir(self))
        return max([self.__getattribute__(column) for column in count_columns])


class CollectionQuerySet(models.QuerySet):
    def visible(self):
        # https://docs.djangoproject.com/en/3.2/ref/models/expressions/#some-examples
        active_jobs = Job.objects.filter(collection=models.OuterRef("pk"), active=True)
        return self.filter(models.Exists(active_jobs), public=True)


class Collection(models.Model):
    class Meta:
        verbose_name = "publication"

    title = models.TextField(
        help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/'
        '14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, '
        "and omitting the country name."
    )

    country = models.TextField(
        blank=True, help_text="The official name of the country from which the data originates."
    )
    country_flag = models.TextField(blank=True)

    language = models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".')
    description = MarkdownxField(
        blank=True,
        help_text="The first paragraph of the description of the publication, as Markdown text, following the <a "
        'href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#'
        'heading=h.fksp8fxgoi7v">template and guidance</a>.',
    )
    description_long = MarkdownxField(
        blank=True,
        help_text="The remaining paragraphs of the description of the publication, as "
        'Markdown text, which will appear under "Show more".',
    )
    last_update = models.DateField(
        blank=True,
        null=True,
        verbose_name="last retrieved",
        help_text="The date on which the most recent 'collect' job task completed.",
    )

    license_custom = models.ForeignKey(
        "License",
        related_name="collection",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="data license",
        help_text="If not set, the Overview section will display " "the license URL within the OCDS package.",
    )

    source_id = models.TextField(
        verbose_name="source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, "
        "Kingfisher Collect needs to be re-deployed to the registry's server.",
    )

    source_url = models.TextField(blank=True, verbose_name="source URL", help_text="The URL of the publication.")

    class Frequency(models.TextChoices):
        MONTHLY = "MONTHLY", _("Monthly")
        HALF_YEARLY = "HALF_YEARLY", _("Every 6 months")
        ANNUALLY = "ANNUALLY", _("Annually")

    update_frequency = models.TextField(
        choices=Frequency.choices,
        blank=True,
        help_text="The frequency at which the registry updates the publication, based on the "
        "frequency at which the publication is updated.",
    )

    summary = MarkdownxField(
        blank=True,
        verbose_name="quality summary",
        help_text="A short summary of quality issues, as Markdown text. Individual issues can be "
        "described below, which will be rendered as a bullet list.",
    )

    last_reviewed = models.DateField(
        blank=True,
        null=True,
        verbose_name="last reviewed",
        help_text="The date on which the quality summary was last confirmed to be correct. "
        "Only the year and month are published.",
    )

    additional_data = MarkdownxField(
        blank=True,
        verbose_name="data availability",
        help_text="Any notable highlights about the available data, such as extensions "
        "used or additional fields, as Markdown text.",
    )

    json_format = models.BooleanField(default=True)
    excel_format = models.BooleanField(default=True)
    csv_format = models.BooleanField(default=True)

    public = models.BooleanField(
        default=False,
        help_text="If the active job's tasks completed without errors and all the fields below in "
        "all languages are filled in, check this box to make the publication visible to "
        "anonymous users. Otherwise, it is visible to administrators only.",
    )
    frozen = models.BooleanField(
        default=False, help_text="If the spider is broken, check this box to prevent the scheduling of new jobs."
    )

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    objects = CollectionQuerySet.as_manager()

    def __str__(self):
        return f"{self.title} ({self.id})"


class License(models.Model):
    class Meta:
        verbose_name = "data license"

    name = models.TextField(blank=True, help_text="The official name of the license.")
    description = MarkdownxField(
        blank=True,
        help_text="A brief description of the permissions, conditions and limitations, as " "Markdown text.",
    )
    url = models.TextField(blank=True, verbose_name="URL", help_text="The canonical URL of the license.")

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Issue(models.Model):
    class Meta:
        verbose_name = "quality issue"

    description = MarkdownxField(help_text="A one-line description of the quality issue, as Markdown text.")
    collection = models.ForeignKey("Collection", related_name="issue", on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)


class Task(models.Model):
    class Meta:
        verbose_name = "job task"

    job = models.ForeignKey("Job", related_name="task", on_delete=models.CASCADE)
    start = models.DateTimeField(blank=True, null=True, db_index=True)
    end = models.DateTimeField(blank=True, null=True, db_index=True)

    class Status(models.TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = models.TextField(choices=Status.choices, blank=True)

    class Result(models.TextChoices):
        OK = "OK", "OK"
        FAILED = "FAILED", "FAILED"

    result = models.TextField(choices=Result.choices, blank=True)
    note = models.TextField(blank=True, help_text="Metadata about any failure.")
    context = models.JSONField(blank=True, default=dict)

    type = models.TextField(blank=True)
    order = models.IntegerField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"#{self.id}({self.type})"
