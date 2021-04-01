from django.contrib.postgres.aggregates import ArrayAgg
from django.shortcuts import render
from django.urls import reverse

from data_registry.models import Collection
from data_registry.views.serializers import CollectionSerializer


def index(request):
    response = render(request, 'index.html')

    return response


def search(request):
    results = Collection.objects.all()

    collections = []
    for r in results:
        n = CollectionSerializer.serialize(r)
        n["detail_url"] = reverse("detail", kwargs={"id": r.id})
        collections.append(n)

    return render(request, 'search.html', {"collections": collections})


def detail(request, id):
    data = CollectionSerializer.serialize(
        Collection.objects
                  .annotate(issues=ArrayAgg("issue__description"))
                  .get(id=id)
    )

    return render(request, 'detail.html', {'data': data})
