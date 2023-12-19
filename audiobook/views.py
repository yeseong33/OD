from django.shortcuts import render


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
    pass


def voice_celebrity(request):
    pass


def voice_custom_upload(request):
    pass


def voice_custom_complete(request):
    pass