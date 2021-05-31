import datetime

from django.forms.models import model_to_dict


class BasicSerializer():
    @staticmethod
    def serialize(data):
        result = model_to_dict(data)

        for key, value in result.items():
            if isinstance(value, datetime.date):
                result[key] = value.strftime("%Y-%m-%d")

        return result

    @classmethod
    def serializeQuerySet(cls, items):
        result = []
        for n in items:
            result.append(cls.serialize(n))

        return result


class LicenseSerializer(BasicSerializer):
    pass


class CollectionSerializer(BasicSerializer):
    @staticmethod
    def serialize(data):
        result = BasicSerializer.serialize(data)

        if hasattr(data, "issues") and data.issues:
            result["issues"] = data.issues
        if hasattr(data, "active_job") and data.active_job:
            result["active_job"] = data.active_job
        if hasattr(data, "license_custom") and data.license_custom:
            result["license_custom"] = LicenseSerializer.serialize(data.license_custom)

        return result
