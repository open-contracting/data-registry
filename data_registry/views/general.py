from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render

from data_registry.models import Collection


def index(request):
    response = render(request, 'index.html')

    return response


def search(request):
    response = render(request, 'search.html')

    return response


def collections(request):
    collections = Collection.objects.all()
    return JsonResponse([model_to_dict(c) for c in collections], safe=False)
