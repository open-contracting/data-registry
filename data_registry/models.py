import requests
from django import forms
from django.conf import settings
from django.db.models import JSONField, Model, TextChoices, TextField
from django.db.models.deletion import CASCADE
from django.db.models.expressions import Case, When
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey
from markdownx.models import MarkdownxField
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationTabularInline


class Collection(Model):
    title = TextField()
    ocds_label = CharField(max_length=2048, blank=True, null=True)
    country = CharField(max_length=2048)
    language = CharField(max_length=2048, blank=True, null=True)
    description = TextField(blank=True, null=True)
    description_long = MarkdownxField(blank=True, null=True)
    date_from = DateField(blank=True, null=True)
    date_to = DateField(blank=True, null=True)
    last_update = DateField(blank=True, null=True)
    country = CharField(max_length=2048, blank=True, null=True)
    ocid_prefix = CharField(max_length=2048, blank=True, null=True)

    license = CharField(max_length=2048, blank=True, null=True)
    license_custom = ForeignKey("License", related_name="collection", on_delete=CASCADE, blank=True, null=True)

    source_id = CharField(max_length=2048)

    class Frequency(TextChoices):
        MONTHLY = "MONTHLY", "MONTHLY"
        HALF_YEARLY = "HALF_YEARLY", "HALF_YEARLY"
        ANNUALLY = "ANNUALLY", "ANNUALLY"

    update_frequency = CharField(max_length=2048, choices=Frequency.choices, blank=True, null=True)

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

    summary = MarkdownxField(blank=True, null=True)

    additional_data = MarkdownxField(blank=True, null=True)

    json_format = BooleanField(default=False)
    excel_format = BooleanField(default=False)

    public = BooleanField(default=True)
    frozen = BooleanField(default=False)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.title} ({self.id})"


class License(Model):
    name = CharField(max_length=2048, blank=True, null=True)
    description = TextField()
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

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.format_datetime(self.start)} .. {self.format_datetime(self.end)} ({self.id})"

    def format_datetime(self, dt):
        return dt.strftime('%d-%b-%y') if dt else ""


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


class IssueInLine(TranslationTabularInline):
    model = Issue
    extra = 0


class CollectionAdminForm(forms.ModelForm):
    source_id = forms.ChoiceField(choices=[])
    active_job = forms.ModelChoiceField(queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        super(CollectionAdminForm, self).__init__(*args, **kwargs)

        resp = requests.get(
            settings.SCRAPY_HOST + "listspiders.json",
            params={
                "project": settings.SCRAPY_PROJECT
            }
        )

        json = resp.json()

        if json.get("status") == "ok":
            self.fields['source_id'].choices += tuple([(n, n) for n in json.get("spiders")])

        self.fields["active_job"].queryset = Job.objects.filter(collection=kwargs.get("instance"),
                                                                status=Job.Status.COMPLETED)
        self.fields["active_job"].initial = Job.objects.filter(collection=kwargs.get("instance"), active=True).first()

    def save(self, *args, **kwargs):
        jobs = Job.objects.filter(collection=self.instance)

        active_job = self.cleaned_data["active_job"]
        if active_job:
            jobs.update(active=Case(
                When(id=active_job.id, then=True),
                default=False,
                output_field=BooleanField()
            ))
        else:
            jobs.update(active=False)

        return super(CollectionAdminForm, self).save(*args, **kwargs)


class CollectionAdmin(TabbedDjangoJqueryTranslationAdmin):
    form = CollectionAdminForm
    list_display = ["__str__", "country", "public", "frozen", "active_job"]

    list_editable = ["public", "frozen"]

    inlines = [
        IssueInLine
    ]

    def active_job(self, obj):
        return Job.objects.filter(collection=obj, active=True).first()


class LicenseAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass


class IssueAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass
