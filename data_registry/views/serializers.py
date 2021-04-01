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


class CollectionSerializer(BasicSerializer):
    @staticmethod
    def serialize(data):
        result = BasicSerializer.serialize(data)

        if hasattr(data, "issues") and data.issues:
            result["issues"] = data.issues

        return result
