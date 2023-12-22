from django.shortcuts import render
from django.urls.base import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from .models import *


user_id = 1  # request.user

# 로그인


def index(request):
    return render(request, 'audiobook/index.html')


def login(request):
    return render(request, 'audiobook/login.html')


# 메인화면
class MainView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main.html'

    def get(self, request):
        top_books = Book.objects.all().order_by('-book_likes')[:10]
        user_books = Book.objects.filter(user=user_id)
        hot_books = Book.objects.all().order_by('?')[:10]

        return Response({
            'top_books': top_books,
            'user_books': user_books,
            'hot_books': hot_books
        })


def genre(request):
    pass


def search(request):
    pass


# 청취
def content(request):
    pass


def content_play(request):
    pass


# 성우
def voice_custom(request):
    pass


def voice_celebrity(request):
    pass


def voice_custom_upload(request):
    pass


def voice_custom_complete(request):
    pass
