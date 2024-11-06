from pathlib import Path

import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import widgets
from django.db.models import F

from data_registry import models
from data_registry.util import scrapyd_url

FLAGS_DIR = Path("data_registry/static/img/flags")


class MarkdownWidget(widgets.AdminTextareaWidget):
    class Media:
        css = {"all": ["markdown.css"]}
        js = ["markdown-it.min.js", "markdown.js"]

    template_name = "includes/markdown.html"


class CollectionAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            "title": widgets.AdminTextInputWidget(attrs={"style": "width: 60em"}),  # default 20em
            "country": widgets.AdminTextInputWidget(),
            "language": widgets.AdminTextInputWidget(),
            "source_url": widgets.AdminTextInputWidget(attrs={"style": "width: 60em"}),
            "description": MarkdownWidget(attrs={"rows": 1}),
            "description_long": MarkdownWidget(attrs={"rows": 1}),
            "additional_data": MarkdownWidget(attrs={"rows": 1}),
            "summary": MarkdownWidget(attrs={"rows": 1}),
        }

    source_id = forms.ChoiceField(
        choices=[],
        label="Source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, Kingfisher Collect "
        "needs to be re-deployed to the registry's server.",
    )
    country_flag = forms.ChoiceField(choices=[(None, "---------")], required=False)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        choices = ((self.instance.source_id, self.instance.source_id),)
        if settings.SCRAPYD["url"]:
            try:
                response = requests.get(
                    scrapyd_url("listspiders.json"), params={"project": settings.SCRAPYD["project"]}, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                if data["status"] == "ok":
                    choices += tuple((n, n) for n in data["spiders"])
                else:
                    messages.warning(request, f"Couldn't populate Source ID, because Scrapyd returned error: {data!r}")
            except requests.ConnectionError as e:
                messages.warning(request, f"Couldn't populate Source ID, because Scrapyd connection failed: {e}")
        else:
            messages.warning(request, "Couldn't populate Source ID, because Scrapyd is not configured.")

        self.fields["source_id"].choices += choices

        # https://docs.djangoproject.com/en/4.2/ref/forms/fields/#fields-which-handle-relationships
        # `self.instance.job_set` doesn't work, because `self.instance` might be an unsaved publication.
        #
        # It's not obvious how to use limit_choices_to to filter jobs by collection.
        # https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.ForeignKey.limit_choices_to
        self.fields["active_job"].queryset = (
            models.Job.objects.filter(collection=self.instance).complete().order_by(F("id").desc())
        )

        # Populate choices in the form, not the model, for easier migration between icon sets.
        self.fields["country_flag"].choices += sorted((f.name, f.name) for f in FLAGS_DIR.iterdir() if f.is_file())


class LicenseAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            "name": widgets.AdminTextInputWidget(attrs={"style": "width: 60em"}),
            "url": widgets.AdminTextInputWidget(attrs={"style": "width: 60em"}),
            "description": MarkdownWidget(attrs={"rows": 1}),
        }
