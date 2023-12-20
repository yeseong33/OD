from django.shortcuts import render
from django.urls.base import reverse


def index(request):
    return render(request, 'audiobook/index.html')


def template(request):
    return render(request, 'audiobook/template.html')


def main(request): 
    pass


def genre(request):
    pass


def search(request):
    pass


def content(request):
    pass


def content_play(request):
    pass


def voice_custom(request):
    return render(request, 'audiobook/voice_custom.html')


def voice_celebrity(request):
    pass


def voice_custom_upload(request):
        return render(request, 'audiobook/voice_custom_upload.html')



def voice_custom_complete(request):
    pass
