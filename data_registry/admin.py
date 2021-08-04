from pathlib import Path

import requests
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin, TabularInline
from django.db.models.expressions import Case, When
from django.db.models.fields import BooleanField
from django.forms.widgets import TextInput
from markdownx.widgets import AdminMarkdownxWidget
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationTabularInline

from data_registry.cbom.process import update_collection_availability, update_collection_metadata

from .models import Collection, Issue, Job, License, Task


class IssueInLine(TranslationTabularInline):
    model = Issue
    extra = 0


class CollectionAdminForm(forms.ModelForm):
    source_id = forms.ChoiceField(choices=[])
    active_job = forms.ModelChoiceField(queryset=None, required=False)
    country_flag = forms.ChoiceField(choices=[(None, '---------')], required=False)

    def __init__(self, *args, **kwargs):
        super(CollectionAdminForm, self).__init__(*args, **kwargs)

        try:
            resp = requests.get(
                settings.SCRAPY_HOST + "listspiders.json",
                params={
                    "project": settings.SCRAPY_PROJECT
                }
            )

            json = resp.json()

            if json.get("status") == "ok":
                self.fields['source_id'].choices += tuple([(n, n) for n in json.get("spiders")])
        except Exception:
            # scrapy api doesnt respond
            sid = self.instance.source_id
            self.fields['source_id'].choices += tuple([(sid, sid)])

        self.fields["active_job"].queryset = Job.objects.filter(collection=kwargs.get("instance"),
                                                                status=Job.Status.COMPLETED)
        self.fields["active_job"].initial = Job.objects.filter(collection=kwargs.get("instance"), active=True).first()

        # collect all years from annual dump files names
        flags_dir = "data_registry/static/img/flags"
        files = [f.name for f in Path(flags_dir).glob("*") if f.is_file()]
        files.sort()
        self.fields['country_flag'].choices += tuple([(n, n) for n in files])

    def save(self, *args, **kwargs):
        jobs = Job.objects.filter(collection=self.instance)

        active_job = self.cleaned_data["active_job"]
        if active_job:
            if not active_job.active:
                jobs.update(active=Case(
                    When(id=active_job.id, then=True),
                    default=False,
                    output_field=BooleanField()
                ))

                update_collection_availability(active_job)

                update_collection_metadata(active_job)
        else:
            jobs.update(active=False)

        return super(CollectionAdminForm, self).save(*args, **kwargs)

    class Meta:
        widgets = {
            'title': TextInput(attrs={"class": "vTextField"}),
            'description': AdminMarkdownxWidget(attrs={'cols': 100, 'rows': 3}),
            'description_long': AdminMarkdownxWidget(attrs={'cols': 100, 'rows': 6}),
            'summary': AdminMarkdownxWidget(attrs={'cols': 100, 'rows': 6}),
            'additional_data': AdminMarkdownxWidget(attrs={'cols': 100, 'rows': 6})
        }


class CollectionAdmin(TabbedDjangoJqueryTranslationAdmin):
    form = CollectionAdminForm
    list_display = ["__str__", "country", "public", "frozen", "active_job"]

    list_editable = ["public", "frozen"]

    inlines = [
        IssueInLine
    ]

    def _get_declared_fieldsets(self, request, obj=None):
        return [(None, {'fields': self.replace_orig_field(self.get_fields(request, obj))})]

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        self._f_move(fields, 'source_id', 0)
        self._f_move(fields, 'active_job', 1)
        self._f_move(fields, 'country_en', 2)

        self._f_move_relative(fields, 'country_en', 'country_es')
        self._f_move_relative(fields, 'country_en', 'country_flag')

        return fields

    def _f_move(self, fields, field, index):
        fields.remove(field)
        fields.insert(index, field)

    def _f_move_relative(self, fields, origin, field):
        index = fields.index(origin) + 1
        if index > len(fields) - 1:
            index = len(fields) - 1

        self._f_move(fields, field, index)

    def _f_move_revert(self, fields, field, index=0):
        index = len(fields) - 1 - index

        self._f_move(fields, field, index)

    def active_job(self, obj):
        return Job.objects.filter(collection=obj, active=True).first()


class LicenseAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass


class IssueAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'description': AdminMarkdownxWidget(attrs={'cols': 100, 'rows': 3})
        }


class IssueAdmin(TabbedDjangoJqueryTranslationAdmin):
    form = IssueAdminForm


class TaskInLine(TabularInline):
    model = Task
    extra = 0
    fields = ["type", "status", "result", "context"]
    readonly_fields = ["type", "result", "context"]
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class JobAdmin(ModelAdmin):
    list_display = ["__str__", "country", "collection", "status", "last_task", "active", "archived", "keep_all_data"]

    list_editable = ["active", "status", "keep_all_data"]

    inlines = [
        TaskInLine
    ]

    @admin.display(description='Country')
    def country(self, obj):
        return obj.collection.country

    @admin.display(description='Last completed task')
    def last_task(self, obj):
        last_completed_task = obj.task.values("type", "order")\
            .filter(status=Task.Status.COMPLETED).order_by('-order').first()

        if last_completed_task:
            return f"{last_completed_task.get('type')} ({last_completed_task.get('order')}/4)"

        return None


class TaskAdmin(ModelAdmin):
    list_display = ["__str__", "type", "job", "status", "result"]

    list_editable = ["status"]


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Task, TaskAdmin)
