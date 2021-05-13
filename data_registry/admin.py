from django.contrib import admin

from .models import Collection, CollectionAdmin, Issue, IssueAdmin, License, LicenseAdmin

admin.site.register(Collection, CollectionAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(License, LicenseAdmin)
