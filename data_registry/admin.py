from django.contrib import admin

from .models import Collection, Issue

admin.site.register(Collection)
admin.site.register(Issue)
