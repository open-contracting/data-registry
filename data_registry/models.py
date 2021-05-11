import requests
from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import JSONField, Model, TextChoices, TextField
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey


class Collection(Model):
    title = TextField()
    ocds_label = CharField(max_length=2048, blank=True, null=True)
    country = CharField(max_length=2048, blank=True, null=True)
    language = CharField(max_length=2048, blank=True, null=True)
    description = TextField(blank=True, null=True)
    description_long = TextField(blank=True, null=True)
    date_from = DateField(blank=True, null=True)
    date_to = DateField(blank=True, null=True)
    last_update = DateField(blank=True, null=True)
    country = CharField(max_length=2048, blank=True, null=True)
    ocid_prefix = CharField(max_length=2048, blank=True, null=True)
    license = CharField(max_length=2048, blank=True, null=True)
    source_id = CharField(max_length=2048)

    class Frequency(TextChoices):
        MONTHLY = "MONTHLY", "MONTHLY"
        HALF_YEARLY = "HALF_YEARLY", "HALF_YEARLY"
        ANNUALLY = "ANNUALLY", "ANNUALLY"

    update_frequency = CharField(max_length=2048, choices=Frequency.choices, blank=True, null=True)

    tenders_count = IntegerField(default=0)
    parties_count = IntegerField(default=0)
    awards_count = IntegerField(default=0)
    contracts_count = IntegerField(default=0)
    documents_count = IntegerField(default=0)
    plannings_count = IntegerField(default=0)
    milestones_count = IntegerField(default=0)
    amendments_count = IntegerField(default=0)

    summary = TextField(blank=True, null=True)

    additional_data = TextField(blank=True, null=True)

    json_format = BooleanField(default=False)
    excel_format = BooleanField(default=False)

    public = BooleanField(default=True)
    frozen = BooleanField(default=False)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)


class CollectionAdminForm(forms.ModelForm):
    source_id = forms.ChoiceField(choices=[(None, "-----------")])

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


class CollectionAdmin(admin.ModelAdmin):
    form = CollectionAdminForm


class Issue(Model):
    description = TextField()
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
        return "#" + str(self.id)


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
        return "#{}({})".format(str(self.id), self.type)
