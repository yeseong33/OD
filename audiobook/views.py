from django.shortcuts import render


def index(request):
    return render(request, 'audiobook/index.html')


def template(request):
    return render(request, 'audiobook/template.html')


def custom(request):
    return render(request, 'audiobook/custom.html')