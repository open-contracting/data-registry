from django.db.models import Model, TextField
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey


class Collection(Model):
    title = TextField()
    ocds_label = TextField()
    country = TextField()
    description = TextField(blank=True, null=True)
    date_from = DateField(blank=True, null=True)
    date_to = DateField(blank=True, null=True)
    last_update = DateField(blank=True, null=True)
    country = CharField(max_length=2048, blank=True, null=True)
    ocid_prefix = CharField(max_length=2048, blank=True, null=True)
    license = CharField(max_length=2048, blank=True, null=True)

    FREQUENCY_CHOICES = [
        ("MONTHLY", "MONTHLY"),
        ("HALF_YEARLY", "HALF_YEARLY"),
        ("ANNUALLY", "ANNUALLY")
    ]

    update_frequency = CharField(max_length=2048, choices=FREQUENCY_CHOICES, blank=True, null=True)

    tenders_count = IntegerField(default=0)
    parties_count = IntegerField(default=0)
    awards_count = IntegerField(default=0)
    contracts_count = IntegerField(default=0)
    documents_count = IntegerField(default=0)
    plannings_count = IntegerField(default=0)
    milestones_count = IntegerField(default=0)
    amendments_count = IntegerField(default=0)

    summary = TextField()

    json_format = BooleanField(default=False)
    excel_format = BooleanField(default=False)

    created = DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    modified = DateTimeField(auto_now=True, blank=True, null=True, db_index=True)


class Issue(Model):
    description = TextField()
    collection = ForeignKey("Collection", related_name="issue", on_delete=CASCADE)
