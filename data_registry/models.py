from django.db.models import Model, TextField


class Collection(Model):
    title = TextField()
    ocds_label = TextField()
    country = TextField()
