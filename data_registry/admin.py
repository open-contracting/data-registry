import contextlib
import logging
from collections import defaultdict

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import escape, urlize
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext
from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin, TranslationAdmin

from data_registry import forms
from data_registry.exceptions import RecoverableError
from data_registry.models import Collection, Job, License, Task
from data_registry.util import CHANGE, CHANGELIST, intcomma, partialclass

logger = logging.getLogger(__name__)

TRANSLATION_REMINDER = (
    "<em>Remember to provide information in all languages. You can use the dropdown at the top "
    "of the page to toggle the language for all fields.</em>"
)


class CascadeTaskMixin:
    def delete_queryset(self, request, queryset):
        try:
            super().delete_queryset(request, queryset)
        except RecoverableError as e:
            messages.set_level(request, messages.WARNING)
            messages.error(request, f"Recoverable exception when wiping task: '{e}'. Please try again.")

    def delete_model(self, request, obj):
        try:
            super().delete_model(request, obj)
        except RecoverableError as e:
            messages.set_level(request, messages.WARNING)
            messages.error(request, f"Recoverable exception when wiping task {obj}: '{e}'. Please try again.")


class IncompleteFilter(admin.SimpleListFilter):
    title = "incomplete"
    parameter_name = "incomplete"

    def lookups(self, request, model_admin):
        return (("1", "Yes"),)

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
        return None


class UntranslatedFilter(admin.SimpleListFilter):
    title = "untranslated"
    parameter_name = "untranslated"

    def lookups(self, request, model_admin):
        return (("1", "Yes"),)

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
        return None


class CustomDateFieldListFilter(admin.DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # https://github.com/django/django/blob/4.2/django/contrib/admin/filters.py#L355-L359
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()

        self.links += (
            (
                "Previous year",
                {
                    self.lookup_kwarg_since: str(today.replace(year=today.year - 1, month=1, day=1)),
                    self.lookup_kwarg_until: str(today.replace(month=1, day=1)),
                },
            ),
            (
                "More than a year ago",
                {
                    self.lookup_kwarg_until: str(today.replace(year=today.year - 1)),
                },
            ),
        )


@admin.register(Collection)
class CollectionAdmin(CascadeTaskMixin, TabbedDjangoJqueryTranslationAdmin):
    form = forms.CollectionAdminForm
    actions = ["create_job"]
    search_fields = ["title_en", "country_en"]
    list_display = ["__str__", "country", "public", "frozen", "active_job", "last_reviewed"]
    list_editable = ["public", "frozen"]
    list_filter = [
        "public",
        "frozen",
        ("active_job", admin.EmptyFieldListFilter),
        "retrieval_frequency",
        ("license_custom", admin.EmptyFieldListFilter),
        ("summary_en", admin.EmptyFieldListFilter),
        IncompleteFilter,
        UntranslatedFilter,
        ("last_reviewed", CustomDateFieldListFilter),
    ]

    fieldsets = (
        (
            "Management",
            {
                "fields": (
                    "source_id",
                    "retrieval_frequency",
                    "active_job",
                    "last_retrieved",
                    "frozen",
                    "public",
                ),
            },
        ),
        (
            "Basics",
            {
                "description": TRANSLATION_REMINDER,
                "fields": (
                    "title_en",
                    "title_es",
                    "title_ru",
                    "country_en",
                    "country_es",
                    "country_ru",
                    "country_flag",
                    "region",
                ),
            },
        ),
        (
            "Overview",
            {
                "description": TRANSLATION_REMINDER,
                "fields": (
                    "language_en",
                    "language_es",
                    "language_ru",
                    "update_frequency",
                    "license_custom",
                    "publication_policy",
                    "source_url",
                ),
            },
        ),
        (
            "Details",
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
                    "no_data_rationale_en",
                    "no_data_rationale_es",
                    "no_data_rationale_ru",
                ),
            },
        ),
    )

    readonly_fields = ["last_retrieved"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = partialclass(self.form, request=request)
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["active_job"].widget.can_add_related = False
        return form

    @admin.action(description="Create a job for each selected publication")
    def create_job(self, request, queryset):
        not_created = 0
        created = 0
        for collection in queryset:
            if collection.job_set.incomplete() or collection.is_out_of_date():
                not_created += 1
            else:
                collection.job_set.create()
                created += 1

        message = ngettext("Created %(count)d job.", "Created %(count)d jobs.", created) % {"count": created}
        self.message_user(request, message, messages.SUCCESS)

        if not_created:
            message = ngettext(
                "%(count)d publication either has an incomplete job or will be scheduled shortly.",
                "%(count)d publications either have incomplete jobs or will be scheduled shortly.",
                not_created,
            ) % {"count": not_created}
            self.message_user(request, message, messages.WARNING)
            # Stay on the same page, in case the user wants to retry.
            return None

        return HttpResponseRedirect(reverse(CHANGELIST.format(content_type=ContentType.objects.get_for_model(Job))))


class UnsuccessfulFilter(admin.SimpleListFilter):
    title = "unsuccessful"
    parameter_name = "unsuccessful"

    def lookups(self, request, model_admin):
        return (("1", "Yes"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.unsuccessful()
        return None


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
    list_filter = ["status", ("active_collection", admin.EmptyFieldListFilter), "archived", UnsuccessfulFilter]

    fieldsets = (
        (
            "Management",
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
            "Logs",
            {
                "fields": ("formatted_process_notes",),
            },
        ),
        (
            "Overview",
            {
                "fields": (
                    "date_from",
                    "date_to",
                    "ocid_prefix",
                    "license",
                    "publication_policy",
                ),
            },
        ),
        (
            "Data availability",
            {
                "fields": (
                    "formatted_parties_count",
                    "formatted_plannings_count",
                    "formatted_tenders_count",
                    "formatted_tenderers_count",
                    "formatted_tenders_items_count",
                    "formatted_awards_count",
                    "formatted_awards_items_count",
                    "formatted_awards_suppliers_count",
                    "formatted_contracts_count",
                    "formatted_contracts_items_count",
                    "formatted_contracts_transactions_count",
                    "formatted_documents_count",
                    "formatted_milestones_count",
                    "formatted_amendments_count",
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
        "formatted_process_notes",
        "start",
        "end",
        # Overview
        "date_from",
        "date_to",
        "ocid_prefix",
        "license",
        "publication_policy",
        # Data availability
        "formatted_parties_count",
        "formatted_plannings_count",
        "formatted_tenders_count",
        "formatted_tenderers_count",
        "formatted_tenders_items_count",
        "formatted_awards_count",
        "formatted_awards_items_count",
        "formatted_awards_suppliers_count",
        "formatted_contracts_count",
        "formatted_contracts_items_count",
        "formatted_contracts_transactions_count",
        "formatted_documents_count",
        "formatted_milestones_count",
        "formatted_amendments_count",
    ]

    inlines = [TaskInLine]

    @admin.display(description="Process notes")
    def formatted_process_notes(self, obj):
        html = []

        for level, notes in obj.process_notes.items():
            if notes:
                html.append(f"<h3>{level}</h3>")
                groups = defaultdict(list)
                for note, data in notes:
                    if data:
                        group_name = tuple(data.items())
                    elif note.startswith("Multiple objects have the `id` value "):
                        group_name = "OCDS Merge"
                    else:
                        group_name = "Uncategorized"
                    for line in note.split("\n"):
                        groups[group_name].append(line)

                for group_name, group_notes in groups.items():
                    html.append(f"<details><summary>{escape(group_name)} ({len(group_notes)})</summary><dl>")
                    html.extend(f"<dd>{urlize(escape(note))}</dd>" for note in group_notes)
                    html.append("</dl></details>")

        return mark_safe("".join(html))

    @admin.display(description="Parties")
    def formatted_parties_count(self, obj):
        return intcomma(obj.parties_count)

    @admin.display(description="Planning")
    def formatted_plannings_count(self, obj):
        return intcomma(obj.plannings_count)

    @admin.display(description="Tenders")
    def formatted_tenders_count(self, obj):
        return intcomma(obj.tenders_count)

    @admin.display(description="Tenderers")
    def formatted_tenderers_count(self, obj):
        return intcomma(obj.tenderers_count)

    @admin.display(description="Tender items")
    def formatted_tenders_items_count(self, obj):
        return intcomma(obj.tenders_items_count)

    @admin.display(description="Awards")
    def formatted_awards_count(self, obj):
        return intcomma(obj.awards_count)

    @admin.display(description="Award items")
    def formatted_awards_items_count(self, obj):
        return intcomma(obj.awards_items_count)

    @admin.display(description="Suppliers")
    def formatted_awards_suppliers_count(self, obj):
        return intcomma(obj.awards_suppliers_count)

    @admin.display(description="Contracts")
    def formatted_contracts_count(self, obj):
        return intcomma(obj.contracts_count)

    @admin.display(description="Contract items")
    def formatted_contracts_items_count(self, obj):
        return intcomma(obj.contracts_items_count)

    @admin.display(description="Transactions")
    def formatted_contracts_transactions_count(self, obj):
        return intcomma(obj.contracts_transactions_count)

    @admin.display(description="Documents")
    def formatted_documents_count(self, obj):
        return intcomma(obj.documents_count)

    @admin.display(description="Milestones")
    def formatted_milestones_count(self, obj):
        return intcomma(obj.milestones_count)

    @admin.display(description="Amendments")
    def formatted_amendments_count(self, obj):
        return intcomma(obj.amendments_count)

    @admin.display(description="Country")
    def country(self, obj):
        return obj.collection.country

    @admin.display(description="Active", boolean=True)
    def active(self, obj):
        return obj.pk == obj.collection.active_job_id

    @admin.display(description="Last completed task")
    def last_task(self, obj):
        last_completed_task = (
            obj.task_set.values("type", "order").filter(status=Task.Status.COMPLETED).order_by("-order").first()
        )

        if last_completed_task:
            return f"{last_completed_task['type']} ({last_completed_task['order']}/{len(settings.JOB_TASKS_PLAN)})"

        return None


@admin.register(License)
class LicenseAdmin(TranslationAdmin):
    form = forms.LicenseAdminForm
    list_display = ["__str__", "name_es", "link", "description_length"]

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

    @admin.display(description="URL", ordering="url")
    def link(self, obj):
        return mark_safe(urlize(obj.url))

    @admin.display(description="Lines (characters)")
    def description_length(self, obj):
        # Russian isn't populated in practice: SELECT id, name_ru, description_ru FROM data_registry_license;
        characters = "/".join(str(len(field)) for field in (obj.description_en, obj.description_es))
        lines = "/".join(str(len(field.split("\n"))) for field in (obj.description_en, obj.description_es))
        return f"{lines} ({characters})"


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
            with contextlib.suppress(NoReverseMatch):
                url = reverse(CHANGE.format(content_type=content_type), args=[obj.object_id])
                object_link = f'<a href="{url}">{object_link}</a>'

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
