from pathlib import Path
from urllib.parse import urljoin

import requests
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin.options import ModelAdmin, TabularInline
from django.db.models import BooleanField, Case, Q, When
from django.forms.widgets import TextInput
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from markdownx.widgets import AdminMarkdownxWidget
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationTabularInline

from data_registry.models import Collection, Issue, Job, License, Task

translation_reminder = _(
    "<em>Remember to provide information in all languages. You can use the dropdown at the top "
    "of the page to toggle the language for all fields.</em>"
)


class IssueInLine(TranslationTabularInline):
    model = Issue
    extra = 0


class CollectionAdminForm(forms.ModelForm):
    source_id = forms.ChoiceField(
        choices=[],
        label="Source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, Kingfisher Collect "
        "needs to be re-deployed to the registry's server.",
    )
    active_job = forms.ModelChoiceField(
        queryset=None,
        required=False,
        help_text="A job is a set of tasks to collect and process data from a publication. A job can be selected once "
        "it is completed. If a new job completes, it becomes the active job.",
    )
    country_flag = forms.ChoiceField(choices=[(None, "---------")], required=False)

    def __init__(self, *args, **kwargs):
        super(CollectionAdminForm, self).__init__(*args, **kwargs)

        try:
            url = urljoin(settings.SCRAPYD["url"], "/listspiders.json")
            response = requests.get(url, params={"project": settings.SCRAPYD["project"]})
            response.raise_for_status()

            json = response.json()

            if json.get("status") == "ok":
                self.fields["source_id"].choices += tuple([(n, n) for n in json.get("spiders")])
        except Exception:
            # scrapy api doesnt respond
            sid = self.instance.source_id
            self.fields["source_id"].choices += tuple([(sid, sid)])

        self.fields["active_job"].queryset = Job.objects.filter(
            collection=kwargs.get("instance"), status=Job.Status.COMPLETED
        )
        self.fields["active_job"].initial = Job.objects.filter(collection=kwargs.get("instance"), active=True).first()

        # collect all years from annual dump files names
        flags_dir = "data_registry/static/img/flags"
        files = [f.name for f in Path(flags_dir).glob("*") if f.is_file()]
        files.sort()
        self.fields["country_flag"].choices += tuple([(n, n) for n in files])

    def save(self, *args, **kwargs):
        jobs = Job.objects.filter(collection=self.instance)

        active_job = self.cleaned_data["active_job"]
        if active_job:
            if not active_job.active:
                jobs.update(active=Case(When(id=active_job.id, then=True), default=False, output_field=BooleanField()))
        else:
            jobs.update(active=False)

        return super(CollectionAdminForm, self).save(*args, **kwargs)

    class Meta:
        widgets = {
            "title": TextInput(attrs={"class": "vTextField"}),
            "description": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 3}),
            "description_long": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
            "summary": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
            "additional_data": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
        }


class MissingContentFilter(admin.SimpleListFilter):
    title = _("Incomplete content")

    parameter_name = "incomplete"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        qs = (
            Q(country_flag="")
            | Q(country_en="")
            | Q(country_es="")
            # title_en is required.
            | Q(title_es="")
            | Q(description_en="")
            | Q(description_es="")
            | Q(description_long_en="")
            | Q(description_long_es="")
            | Q(additional_data_en="")
            | Q(additional_data_es="")
            | Q(summary_en="")
            | Q(summary_es="")
            | Q(update_frequency="")
            | Q(license_custom=None)
            | Q(language_en="")
            | Q(language_es="")
            | Q(source_url="")
        )
        if self.value() == "1":
            return queryset.filter(qs)
        if self.value() == "0":
            return queryset.exclude(qs)


class CustomDateFieldListFilter(DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super(CustomDateFieldListFilter, self).__init__(*args, **kwargs)

        # https://github.com/django/django/blob/3.2/django/contrib/admin/filters.py#L312-L316
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()

        self.links += (
            (
                _("Previous year"),
                {
                    self.lookup_kwarg_since: str(today.replace(year=today.year - 1, month=1, day=1)),
                    self.lookup_kwarg_until: str(today.replace(month=1, day=1)),
                },
            ),
            (
                _("More than a year ago"),
                {
                    self.lookup_kwarg_until: str(today.replace(year=today.year - 1)),
                },
            ),
        )


@admin.register(Collection)
class CollectionAdmin(TabbedDjangoJqueryTranslationAdmin):
    form = CollectionAdminForm
    list_display = ["__str__", "country", "public", "frozen", "active_job", "last_reviewed"]
    list_editable = ["public", "frozen"]
    list_filter = ["public", "frozen", ("last_reviewed", CustomDateFieldListFilter), MissingContentFilter]

    # json_format and excel_format will never be disabled in the current version.
    fieldsets = (
        (
            _("Management"),
            {
                "fields": ("source_id", "active_job", "public", "frozen", "last_update"),
            },
        ),
        (
            _("Basics"),
            {
                "description": translation_reminder,
                "fields": (
                    "country_flag",
                    "country_en",
                    "country_es",
                    "country_ru",
                    "title_en",
                    "title_es",
                    "title_ru",
                ),
            },
        ),
        (
            _("Overview"),
            {
                "description": translation_reminder,
                "fields": (
                    "update_frequency",
                    "license_custom",
                    "source_url",
                    "language_en",
                    "language_es",
                    "language_ru",
                ),
            },
        ),
        (
            _("Details"),
            {
                "description": translation_reminder,
                "fields": (
                    "description_en",
                    "description_es",
                    "description_ru",
                    "description_long_en",
                    "description_long_es",
                    "description_long_ru",
                    "additional_data_en",
                    "additional_data_es",
                    "additional_data_ru",
                    "summary_en",
                    "summary_es",
                    "summary_ru",
                    "last_reviewed",
                ),
            },
        ),
    )

    readonly_fields = ["last_update"]

    inlines = [IssueInLine]

    def active_job(self, obj):
        return Job.objects.filter(collection=obj, active=True).first()


class LicenseAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"description": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 3})}


@admin.register(License)
class LicenseAdmin(TabbedDjangoJqueryTranslationAdmin):
    fieldsets = (
        (
            None,
            {
                "description": translation_reminder,
                "fields": (
                    "name_en",
                    "name_es",
                    "name_ru",
                    "description_en",
                    "description_es",
                    "description_ru",
                    "url",
                ),
            },
        ),
    )


class IssueAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"description": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 3})}


class TaskInLine(TabularInline):
    model = Task
    extra = 0
    fields = ["type", "status", "start", "end", "result", "note"]
    readonly_fields = ["type", "start", "end", "result", "note"]
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ["__str__", "country", "collection", "status", "last_task", "active", "archived", "keep_all_data"]

    # Multiple jobs can be set as active for the same collection, so "active" is set as read-only.
    list_editable = ["status", "keep_all_data"]
    fieldsets = (
        (
            _("Management"),
            {
                "fields": (
                    "collection",
                    "active",
                    "status",
                    "context",
                    "keep_all_data",
                    "archived",
                    "start",
                    "end",
                ),
            },
        ),
        (
            _("Overview"),
            {
                "fields": (
                    "date_from",
                    "date_to",
                    "ocid_prefix",
                    "license",
                ),
            },
        ),
        (
            _("Data availability"),
            {
                "fields": (
                    "parties_count",
                    "plannings_count",
                    "tenders_count",
                    "tenderers_count",
                    "tenders_items_count",
                    "awards_count",
                    "awards_items_count",
                    "awards_suppliers_count",
                    "contracts_count",
                    "contracts_items_count",
                    "contracts_transactions_count",
                    "documents_count",
                    "milestones_count",
                    "amendments_count",
                ),
            },
        ),
    )
    readonly_fields = [
        # Only status and keep_all_data are editable.
        "collection",
        "active",
        "archived",
        "context",
        "start",
        "end",
        # Overview
        "date_from",
        "date_to",
        "ocid_prefix",
        "license",
        # Data availability
        "parties_count",
        "plannings_count",
        "tenders_count",
        "tenderers_count",
        "tenders_items_count",
        "awards_count",
        "awards_items_count",
        "awards_suppliers_count",
        "contracts_count",
        "contracts_items_count",
        "contracts_transactions_count",
        "documents_count",
        "milestones_count",
        "amendments_count",
    ]

    inlines = [TaskInLine]

    @admin.display(description="Country")
    def country(self, obj):
        return obj.collection.country

    @admin.display(description="Last completed task")
    def last_task(self, obj):
        last_completed_task = (
            obj.task.values("type", "order").filter(status=Task.Status.COMPLETED).order_by("-order").first()
        )

        if last_completed_task:
            return f"{last_completed_task.get('type')} ({last_completed_task.get('order')}/4)"

        return None
