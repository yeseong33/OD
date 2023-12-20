from django.shortcuts import render


def index(request):
    return render(request, 'audiobook/index.html')


def template(request):
    return render(request, 'audiobook/template.html')

def login(request):
    return render(request, 'audiobook/login.html')
