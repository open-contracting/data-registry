import datetime

from django.forms.models import model_to_dict

from data_registry.utils import markdownify


class BasicSerializer:
    markdown_fields = []

    @classmethod
    def serialize(cls, data):
        result = model_to_dict(data)

        for key, value in result.items():
            if isinstance(value, datetime.datetime):
                result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, datetime.date):
                result[key] = value.strftime("%Y-%m-%d")

            if key in cls.markdown_fields and value:
                if type(value) == list:
                    result[key] = [markdownify(n) for n in value if n]
                else:
                    result[key] = markdownify(value)

        return result

    @classmethod
    def serializeQuerySet(cls, items):
        result = []
        for n in items:
            result.append(cls.serialize(n))

        return result


class LicenseSerializer(BasicSerializer):
    markdown_fields = ["description"]
    pass


class JobSerializer(BasicSerializer):
    pass


class CollectionSerializer(BasicSerializer):
    markdown_fields = ["additional_data", "description", "description_long", "summary", "issues"]

    @classmethod
    def serialize(cls, data):
        result = super(CollectionSerializer, cls).serialize(data)

        if hasattr(data, "issues") and data.issues:
            result["issues"] = [markdownify(description) for description in data.issues]
        if hasattr(data, "license_custom") and data.license_custom:
            result["license_custom"] = LicenseSerializer.serialize(data.license_custom)
        if hasattr(data, "active_job") and data.active_job:
            result["active_job"] = JobSerializer.serialize(data.active_job)

        return result
