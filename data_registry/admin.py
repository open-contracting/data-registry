import requests
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin, TabularInline
from django.db.models.expressions import Case, When
from django.db.models.fields import BooleanField
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationTabularInline

from .models import Collection, Issue, Job, License, Task


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


class TaskInLine(TabularInline):
    model = Task
    extra = 0
    fields = ["type", "status", "result", "context"]
    readonly_fields = ["type", "result", "context"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class JobAdmin(ModelAdmin):
    list_display = ["__str__", "collection", "status", "active"]

    list_editable = ["active", "status"]

    inlines = [
        TaskInLine
    ]


class TaskAdmin(ModelAdmin):
    list_display = ["__str__", "type", "job", "status", "result"]

    list_editable = ["status"]


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Task, TaskAdmin)
