import logging
from pathlib import Path

import requests
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import BooleanField, Case, Q, When
from django.forms.widgets import TextInput
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from markdownx.widgets import AdminMarkdownxWidget
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationTabularInline

from data_registry.exceptions import RecoverableException
from data_registry.models import Collection, Issue, Job, License, Task
from data_registry.util import partialclass, scrapyd_url

logger = logging.getLogger(__name__)

FLAGS_DIR = Path("data_registry/static/img/flags")

TRANSLATION_REMINDER = _(
    "<em>Remember to provide information in all languages. You can use the dropdown at the top "
    "of the page to toggle the language for all fields.</em>"
)


class CascadeTaskMixin:
    def delete_queryset(self, request, queryset):
        try:
            super().delete_queryset(request, queryset)
        except RecoverableException as e:
            messages.set_level(request, messages.WARNING)
            messages.error(request, f"Recoverable exception when wiping task: '{e}'. Please try again.")

    def delete_model(self, request, obj):
        try:
            super().delete_model(request, obj)
        except RecoverableException as e:
            messages.set_level(request, messages.WARNING)
            messages.error(request, f"Recoverable exception when wiping task {obj}: '{e}'. Please try again.")


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

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        choices = ((self.instance.source_id, self.instance.source_id),)
        if settings.SCRAPYD["url"]:
            try:
                response = requests.get(
                    scrapyd_url("listspiders.json"), params={"project": settings.SCRAPYD["project"]}
                )
                response.raise_for_status()
                data = response.json()
                if data["status"] == "ok":
                    choices = tuple((n, n) for n in data["spiders"])
                else:
                    messages.warning(request, f"Couldn't populate Source ID, because Scrapyd returned error: {data!r}")
            except requests.exceptions.ConnectionError as e:
                messages.warning(request, f"Couldn't populate Source ID, because Scrapyd connection failed: {e}")
        else:
            messages.warning(request, "Couldn't populate Source ID, because Scrapyd is not configured.")

        self.fields["source_id"].choices += choices

        # https://docs.djangoproject.com/en/4.2/ref/forms/fields/#fields-which-handle-relationships
        # `self.instance.job_set` doesn't work, because `self.instance` might be an unsaved publication.
        self.fields["active_job"].queryset = Job.objects.filter(collection=self.instance).complete()
        self.fields["active_job"].initial = Job.objects.filter(collection=self.instance).active().first()

        # Populate choices in the form, not the model, for easier migration between icon sets.
        self.fields["country_flag"].choices += sorted((f.name, f.name) for f in FLAGS_DIR.iterdir() if f.is_file())

    def save(self, *args, **kwargs):
        jobs = self.instance.job_set

        active_job = self.cleaned_data["active_job"]
        if active_job:
            if not active_job.active:
                jobs.update(active=Case(When(id=active_job.id, then=True), default=False, output_field=BooleanField()))
        elif self.instance.pk:
            jobs.update(active=False)

        return super().save(*args, **kwargs)

    class Meta:
        widgets = {
            "title": TextInput(attrs={"class": "vTextField"}),
            "description": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 3}),
            "description_long": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
            "summary": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
            "additional_data": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 6}),
        }


class IncompleteFilter(admin.SimpleListFilter):
    title = _("incomplete")

    parameter_name = "incomplete"

    def lookups(self, request, model_admin):
        return (("1", _("Yes")),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(
                Q(country_en="")
                | Q(country_flag="")
                | Q(language_en="")
                | Q(description_en="")
                | Q(source_url="")
                | Q(retrieval_frequency="")
                | Q(additional_data_en="")
            )


class UntranslatedFilter(admin.SimpleListFilter):
    title = _("untranslated")

    parameter_name = "untranslated"

    def lookups(self, request, model_admin):
        return (("1", _("Yes")),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(
                (~Q(title_en="") & Q(title_es=""))
                | (~Q(country_en="") & Q(country_es=""))
                | (~Q(language_en="") & Q(language_es=""))
                | (~Q(description_en="") & Q(description_es=""))
                | (~Q(description_long_en="") & Q(description_long_es=""))
                | (~Q(summary_en="") & Q(summary_es=""))
                | (~Q(additional_data_en="") & Q(additional_data_es=""))
            )


class CustomDateFieldListFilter(admin.DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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


# https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#logentry-objects
@admin.register(admin.models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display_links = None
    search_fields = [
        "object_repr",
        "change_message",
    ]
    list_display = [
        "action_time",
        "user",
        "content_type",
        "object_link",
        "action_flag",
        "get_change_message",
    ]
    list_filter = [
        "content_type",
        "action_flag",
        "action_time",
    ]

    # https://github.com/liangliangyy/DjangoBlog/blob/master/djangoblog/logentryadmin.py
    @admin.display(ordering="object_repr", description="object")
    def object_link(self, obj):
        object_link = escape(obj.object_repr)
        content_type = obj.content_type  # nullable

        if content_type and obj.action_flag != admin.models.DELETION:
            try:
                # https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#reversing-admin-urls
                url = reverse(f"admin:{content_type.app_label}_{content_type.model}_change", args=[obj.object_id])
                object_link = f'<a href="{url}">{object_link}</a>'
            except NoReverseMatch:
                pass

        return mark_safe(object_link)

    # Avoid N+1 query.
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("content_type")

    # Make it read-only.

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


@admin.register(Collection)
class CollectionAdmin(CascadeTaskMixin, TabbedDjangoJqueryTranslationAdmin):
    form = CollectionAdminForm
    search_fields = ["title_en", "country_en"]
    list_display = ["__str__", "country", "public", "frozen", "active_job", "last_reviewed"]
    list_editable = ["public", "frozen"]
    list_filter = [
        "public",
        "frozen",
        ("license_custom", admin.EmptyFieldListFilter),
        ("summary_en", admin.EmptyFieldListFilter),
        IncompleteFilter,
        UntranslatedFilter,
        ("last_reviewed", CustomDateFieldListFilter),
    ]

    fieldsets = (
        (
            _("Management"),
            {
                "fields": ("source_id", "active_job", "public", "frozen", "last_retrieved"),
            },
        ),
        (
            _("Basics"),
            {
                "description": TRANSLATION_REMINDER,
                "fields": (
                    "country_flag",
                    "country_en",
                    "country_es",
                    "country_ru",
                    "region",
                    "title_en",
                    "title_es",
                    "title_ru",
                ),
            },
        ),
        (
            _("Overview"),
            {
                "description": TRANSLATION_REMINDER,
                "fields": (
                    "retrieval_frequency",
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
                "description": TRANSLATION_REMINDER,
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

    readonly_fields = ["last_retrieved"]

    inlines = [IssueInLine]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = partialclass(self.form, request=request)
        return super().get_form(request, obj, **kwargs)

    def active_job(self, obj):
        return obj.job_set.active().first()


class LicenseAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"description": AdminMarkdownxWidget(attrs={"cols": 100, "rows": 3})}


@admin.register(License)
class LicenseAdmin(TabbedDjangoJqueryTranslationAdmin):
    fieldsets = (
        (
            None,
            {
                "description": TRANSLATION_REMINDER,
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


class TaskInLine(admin.TabularInline):
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
class JobAdmin(CascadeTaskMixin, admin.ModelAdmin):
    class Media:
        css = {"all": ["admin.css"]}

    search_fields = ["collection__title_en", "collection__country_en"]
    list_display = ["__str__", "country", "collection", "status", "last_task", "active", "archived", "keep_all_data"]
    # "active" is read-only and uneditable, because at most one job must be set as active for a given collection.
    list_editable = ["status", "keep_all_data"]
    list_filter = ["status", "active", "archived"]

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
            obj.task_set.values("type", "order").filter(status=Task.Status.COMPLETED).order_by("-order").first()
        )

        if last_completed_task:
            return f"{last_completed_task['type']} ({last_completed_task['order']}/{len(settings.JOB_TASKS_PLAN)})"

        return None
