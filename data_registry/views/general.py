from django.shortcuts import render


def index(request):
    response = render(request, 'index.html')

    return response


def search(request):
    response = render(request, 'search.html')

    return response
