from django.db.models import JSONField, Model, TextChoices, TextField
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey
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

    status = CharField(max_length=2048, choices=Status.choices, blank=True)

    context = JSONField(blank=True, null=True,
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
                                  "</dl>")

    active = BooleanField(default=False,
                          help_text="Set this as the active job for the publication from the publication's page.")

    archived = BooleanField(default=False, verbose_name="temporary data deleted",
                            help_text="Whether the temporary data created by job tasks has been deleted.")

    keep_all_data = BooleanField(default=False, verbose_name="preserve temporary data",
                                 help_text="By default, temporary data created by job tasks is deleted after the job "
                                           "is completed. Only the data registry's models' data and JSON exports are "
                                           "retained. To preserve temporary data for debugging, check this box. Then, "
                                           "when ready, uncheck this box and run the \"cbom\" management command.")

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
    ocid_prefix = CharField(max_length=2048, blank=True, verbose_name="OCID prefix")
    license = CharField(max_length=2048, blank=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.format_datetime(self.start)} .. {self.format_datetime(self.end)} ({self.id})"

    def format_datetime(self, dt):
        return dt.strftime('%d-%b-%y') if dt else ""


class Collection(Model):
    class Meta:
        verbose_name = "publication"

    title = TextField(
        help_text="The name of the publication, following the <a href=\"https://docs.google.com/document/d/"
                  "14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry\">naming conventions</a>, "
                  "and omitting the country name."
    )

    country = CharField(max_length=2048, blank=True,
                        help_text="The official name of the country from which the data originates.")
    country_flag = CharField(max_length=2048, blank=True)

    language = CharField(max_length=2048, blank=True,
                         help_text="The languages used within data fields: for example, \"Spanish\".")
    description = MarkdownxField(
        blank=True,
        help_text="The first paragraph of the description of the publication, as Markdown text, following the <a "
                  "href=\"https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#"
                  "heading=h.fksp8fxgoi7v\">template and guidance</a>.")
    description_long = MarkdownxField(blank=True,
                                      help_text="The remaining paragraphs of the description of the publication, as "
                                                "Markdown text, which will appear under \"Show more\".")
    last_update = DateField(blank=True, null=True, verbose_name="last retrieved",
                            help_text="The date on which the most recent 'scrape' job task completed.")

    license_custom = ForeignKey("License", related_name="collection", on_delete=CASCADE, blank=True, null=True,
                                verbose_name="data license", help_text="If not set, the Overview section will display "
                                                                       "the license URL within the OCDS package.")

    source_id = CharField(max_length=2048, verbose_name="source ID",
                          help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, "
                                    "Kingfisher Collect needs to be re-deployed to the registry's server.")

    source_url = TextField(blank=True, verbose_name="source URL",
                           help_text="The URL of the publication.")

    class Frequency(TextChoices):
        MONTHLY = "MONTHLY", "MONTHLY"
        HALF_YEARLY = "HALF_YEARLY", "HALF_YEARLY"
        ANNUALLY = "ANNUALLY", "ANNUALLY"

    update_frequency = CharField(max_length=2048, choices=Frequency.choices, blank=True,
                                 help_text="The frequency at which the registry updates the publication, based on the "
                                           "frequency at which the publication is updated.")

    summary = MarkdownxField(blank=True, verbose_name="quality summary",
                             help_text="A short summary of quality issues, as Markdown text. Individual issues can be "
                                       "described below, which will be rendered as a bullet list.")

    last_reviewed = DateField(blank=True, null=True, verbose_name="last reviewed",
                              help_text="The date on which the quality summary was last confirmed to be correct. "
                                        "Only the year and month are published.")

    additional_data = MarkdownxField(blank=True, verbose_name="data availability",
                                     help_text="Any notable highlights about the available data, such as extensions "
                                               "used or additional fields, as Markdown text.")

    json_format = BooleanField(default=True)
    excel_format = BooleanField(default=True)

    public = BooleanField(default=False,
                          help_text="If the active job's tasks completed without errors and all the fields below in "
                                    "all languages are filled in, check this box to make the publication visible to "
                                    "anonymous users. Otherwise, it is visible to administrators only.")
    frozen = BooleanField(default=False,
                          help_text="If the spider is broken, check this box to prevent the scheduling of new jobs.")

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    # active job cache
    _active_job = None

    @property
    def active_job(self):
        if not self._active_job:
            self._active_job = Job.objects.filter(active=True, collection=self).first()

        return self._active_job

    @property
    def tenders_count(self):
        return getattr(self.active_job, "tenders_count", 0)

    @property
    def tenderers_count(self):
        return getattr(self.active_job, "tenderers_count", 0)

    @property
    def tenders_items_count(self):
        return getattr(self.active_job, "tenders_items_count", 0)

    @property
    def parties_count(self):
        return getattr(self.active_job, "parties_count", 0)

    @property
    def awards_count(self):
        return getattr(self.active_job, "awards_count", 0)

    @property
    def awards_items_count(self):
        return getattr(self.active_job, "awards_items_count", 0)

    @property
    def awards_suppliers_count(self):
        return getattr(self.active_job, "awards_suppliers_count", 0)

    @property
    def contracts_count(self):
        return getattr(self.active_job, "contracts_count", 0)

    @property
    def contracts_items_count(self):
        return getattr(self.active_job, "contracts_items_count", 0)

    @property
    def contracts_transactions_count(self):
        return getattr(self.active_job, "contracts_transactions_co", 0)

    @property
    def documents_count(self):
        return getattr(self.active_job, "documents_count", 0)

    @property
    def plannings_count(self):
        return getattr(self.active_job, "plannings_count", 0)

    @property
    def milestones_count(self):
        return getattr(self.active_job, "milestones_count", 0)

    @property
    def amendments_count(self):
        return getattr(self.active_job, "amendments_count", 0)

    @property
    def date_from(self):
        return getattr(self.active_job, "date_from", None)

    @property
    def date_to(self):
        return getattr(self.active_job, "date_to", None)

    @property
    def license(self):
        return getattr(self.active_job, "license", None)

    @property
    def ocid_prefix(self):
        return getattr(self.active_job, "ocid_prefix", None)

    def __str__(self):
        return f"{self.title} ({self.id})"


class License(Model):
    class Meta:
        verbose_name = "data license"

    name = CharField(max_length=2048, blank=True,
                     help_text="The official name of the license.")
    description = MarkdownxField(blank=True,
                                 help_text="A brief description of the permissions, conditions and limitations, as "
                                           "Markdown text.")
    url = CharField(max_length=2048, blank=True, verbose_name="URL",
                    help_text="The canonical URL of the license.")

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

    status = CharField(max_length=2048, choices=Status.choices, blank=True)

    class Result(TextChoices):
        OK = "OK", "OK"
        FAILED = "FAILED", "FAILED"

    result = CharField(max_length=2048, choices=Result.choices, blank=True)
    note = TextField(blank=True, help_text="Metadata about any failure.")
    context = JSONField(blank=True, null=True)

    type = CharField(max_length=2048, blank=True)
    order = IntegerField(blank=True, null=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"#{self.id}({self.type})"
