from django.db.models import (
    CASCADE,
    BooleanField,
    DateField,
    DateTimeField,
    Exists,
    ForeignKey,
    IntegerField,
    JSONField,
    Manager,
    Model,
    OuterRef,
    TextChoices,
    TextField,
)
from django.utils.translation import gettext_lazy as _
from markdownx.models import MarkdownxField


class Job(Model):
    collection = ForeignKey("Collection", related_name="job", on_delete=CASCADE, verbose_name="publication")
    start = DateTimeField(blank=True, null=True, db_index=True, verbose_name="job started at")
    end = DateTimeField(blank=True, null=True, db_index=True, verbose_name="job ended at")

    class Status(TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = TextField(choices=Status.choices, blank=True)

    context = JSONField(
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

    active = BooleanField(
        default=False, help_text="Set this as the active job for the publication from the publication's page."
    )

    archived = BooleanField(
        default=False,
        verbose_name="temporary data deleted",
        help_text="Whether the temporary data created by job tasks has been deleted.",
    )

    keep_all_data = BooleanField(
        default=False,
        verbose_name="preserve temporary data",
        help_text="By default, temporary data created by job tasks is deleted after the job "
        "is completed. Only the data registry's models' data and JSON exports are "
        "retained. To preserve temporary data for debugging, check this box. Then, "
        'when ready, uncheck this box and run the "manageprocess" management command.',
    )

    tenders_count = IntegerField(default=0)
    tenderers_count = IntegerField(default=0)
    tenders_items_count = IntegerField(default=0)
    parties_count = IntegerField(default=0)
    awards_count = IntegerField(default=0)
    awards_items_count = IntegerField(default=0)
    awards_suppliers_count = IntegerField(default=0)
    contracts_count = IntegerField(default=0)
    contracts_items_count = IntegerField(default=0)
    contracts_transactions_count = IntegerField(default=0)
    documents_count = IntegerField(default=0)
    plannings_count = IntegerField(default=0)
    milestones_count = IntegerField(default=0)
    amendments_count = IntegerField(default=0)

    date_from = DateField(blank=True, null=True, verbose_name="minimum release date")
    date_to = DateField(blank=True, null=True, verbose_name="maximum release date")
    ocid_prefix = TextField(blank=True, verbose_name="OCID prefix")
    license = TextField(blank=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.format_datetime(self.start)} .. {self.format_datetime(self.end)} ({self.id})"

    def format_datetime(self, dt):
        return dt.strftime("%d-%b-%y") if dt else ""


class PublicCollectionManager(Manager):
    def get_queryset(self):
        # https://docs.djangoproject.com/en/3.2/ref/models/expressions/#some-examples
        active_jobs = Job.objects.filter(collection=OuterRef("pk"), active=True)
        return super().get_queryset().filter(Exists(active_jobs), public=True)


class Collection(Model):
    class Meta:
        verbose_name = "publication"

    title = TextField(
        help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/'
        '14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, '
        "and omitting the country name."
    )

    country = TextField(blank=True, help_text="The official name of the country from which the data originates.")
    country_flag = TextField(blank=True)

    language = TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".')
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
    last_update = DateField(
        blank=True,
        null=True,
        verbose_name="last updated",
        help_text="The date on which the most recent 'collect' job task completed.",
    )

    license_custom = ForeignKey(
        "License",
        related_name="collection",
        on_delete=CASCADE,
        blank=True,
        null=True,
        verbose_name="data license",
        help_text="If not set, the Overview section will display " "the license URL within the OCDS package.",
    )

    source_id = TextField(
        verbose_name="source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, "
        "Kingfisher Collect needs to be re-deployed to the registry's server.",
    )

    source_url = TextField(blank=True, verbose_name="source URL", help_text="The URL of the publication.")

    class Frequency(TextChoices):
        MONTHLY = "MONTHLY", _("Monthly")
        HALF_YEARLY = "HALF_YEARLY", _("Every 6 months")
        ANNUALLY = "ANNUALLY", _("Annually")

    update_frequency = TextField(
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

    last_reviewed = DateField(
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

    json_format = BooleanField(default=True)
    excel_format = BooleanField(default=True)
    csv_format = BooleanField(default=True)

    public = BooleanField(
        default=False,
        help_text="If the active job's tasks completed without errors and all the fields below in "
        "all languages are filled in, check this box to make the publication visible to "
        "anonymous users. Otherwise, it is visible to administrators only.",
    )
    frozen = BooleanField(
        default=False, help_text="If the spider is broken, check this box to prevent the scheduling of new jobs."
    )

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    objects = Manager()
    visible = PublicCollectionManager()

    def __str__(self):
        return f"{self.title} ({self.id})"


class License(Model):
    class Meta:
        verbose_name = "data license"

    name = TextField(blank=True, help_text="The official name of the license.")
    description = MarkdownxField(
        blank=True,
        help_text="A brief description of the permissions, conditions and limitations, as " "Markdown text.",
    )
    url = TextField(blank=True, verbose_name="URL", help_text="The canonical URL of the license.")

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Issue(Model):
    class Meta:
        verbose_name = "quality issue"

    description = MarkdownxField(help_text="A one-line description of the quality issue, as Markdown text.")
    collection = ForeignKey("Collection", related_name="issue", on_delete=CASCADE)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)


class Task(Model):
    class Meta:
        verbose_name = "job task"

    job = ForeignKey("Job", related_name="task", on_delete=CASCADE)
    start = DateTimeField(blank=True, null=True, db_index=True)
    end = DateTimeField(blank=True, null=True, db_index=True)

    class Status(TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = TextField(choices=Status.choices, blank=True)

    class Result(TextChoices):
        OK = "OK", "OK"
        FAILED = "FAILED", "FAILED"

    result = TextField(choices=Result.choices, blank=True)
    note = TextField(blank=True, help_text="Metadata about any failure.")
    context = JSONField(blank=True, default=dict)

    type = TextField(blank=True)
    order = IntegerField(blank=True, null=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"#{self.id}({self.type})"
