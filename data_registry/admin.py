from django.contrib import admin

from .models import Collection, CollectionAdmin, Issue

admin.site.register(Collection, CollectionAdmin)
admin.site.register(Issue)
