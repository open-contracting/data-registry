from django.db.models import JSONField, Model, TextChoices, TextField
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey
from markdownx.models import MarkdownxField


class Job(Model):
    collection = ForeignKey("Collection", related_name="job", on_delete=CASCADE)
    start = DateTimeField(blank=True, null=True, db_index=True)
    end = DateTimeField(blank=True, null=True, db_index=True)

    class Status(TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = CharField(max_length=2048, choices=Status.choices, blank=True, null=True)

    context = JSONField(blank=True, null=True)

    active = BooleanField(default=False)

    archived = BooleanField(default=False)

    keep_all_data = BooleanField(default=False)

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

    date_from = DateField(blank=True, null=True)
    date_to = DateField(blank=True, null=True)
    ocid_prefix = CharField(max_length=2048, blank=True, null=True)
    license = CharField(max_length=2048, blank=True, null=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.format_datetime(self.start)} .. {self.format_datetime(self.end)} ({self.id})"

    def format_datetime(self, dt):
        return dt.strftime('%d-%b-%y') if dt else ""


class Collection(Model):
    title = TextField()

    country = CharField(max_length=2048, blank=True, null=True)
    country_flag = CharField(max_length=2048, blank=True, null=True)

    language = CharField(max_length=2048, blank=True, null=True)
    description = MarkdownxField(blank=True, null=True)
    description_long = MarkdownxField(blank=True, null=True)
    last_update = DateField(blank=True, null=True)

    license_custom = ForeignKey("License", related_name="collection", on_delete=CASCADE, blank=True, null=True)

    source_id = CharField(max_length=2048)

    class Frequency(TextChoices):
        MONTHLY = "MONTHLY", "MONTHLY"
        HALF_YEARLY = "HALF_YEARLY", "HALF_YEARLY"
        ANNUALLY = "ANNUALLY", "ANNUALLY"

    update_frequency = CharField(max_length=2048, choices=Frequency.choices, blank=True, null=True)

    summary = MarkdownxField(blank=True, null=True)

    additional_data = MarkdownxField(blank=True, null=True)

    json_format = BooleanField(default=True)
    excel_format = BooleanField(default=True)

    public = BooleanField(default=True)
    frozen = BooleanField(default=False)

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
    name = CharField(max_length=2048, blank=True, null=True)
    description = MarkdownxField(blank=True, null=True)
    url = CharField(max_length=2048, blank=True, null=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Issue(Model):
    description = MarkdownxField()
    collection = ForeignKey("Collection", related_name="issue", on_delete=CASCADE)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)


class Task(Model):
    job = ForeignKey("Job", related_name="task", on_delete=CASCADE)
    start = DateTimeField(blank=True, null=True, db_index=True)
    end = DateTimeField(blank=True, null=True, db_index=True)

    class Status(TextChoices):
        WAITING = "WAITING", "WAITING"
        PLANNED = "PLANNED", "PLANNED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETED = "COMPLETED", "COMPLETED"

    status = CharField(max_length=2048, choices=Status.choices, blank=True, null=True)

    class Result(TextChoices):
        OK = "OK", "OK"
        FAILED = "FAILED", "FAILED"

    result = CharField(max_length=2048, choices=Result.choices, blank=True, null=True)
    note = TextField(blank=True, null=True)
    context = JSONField(blank=True, null=True)

    type = CharField(max_length=2048, blank=True, null=True)
    order = IntegerField(blank=True, null=True)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"#{self.id}({self.type})"
