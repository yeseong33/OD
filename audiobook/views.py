import os
from dotenv import load_dotenv
import requests
from django.shortcuts import render, redirect
from django.urls.base import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import VoiceSerializer
from .models import *
from user.views import decode_jwt

load_dotenv()


user_id = 1  # request.user

# 첫 화면


def index(request):
    return render(request, 'audiobook/index.html')


# 메인화면
class MainView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main.html'

    def get(self, request):
        top_books = Book.objects.all().order_by('-book_likes')[:10]
        user_books = Book.objects.filter(user=user_id)
        hot_books = Book.objects.all().order_by('?')[:10]

        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        return Response({
            'top_books': top_books,
            'user_books': user_books,
            'hot_books': hot_books,
            'user': user,
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
    return render(request, 'audiobook/voice_custom.html')


def voice_celebrity(request):
    pass


def voice_custom_upload(request):
    return render(request, 'audiobook/voice_custom_upload.html')


def voice_custom_complete(request):
    return render(request, 'audiobook/voice_custom_complete.html')


@api_view(['GET'])
def helloAPI(request):
    return Response("hello world!")


@api_view(["GET", "POST"])
def voice_search(request):
    if request.method == 'GET':
        voices = Voice.objects.all()
        serializer = VoiceSerializer(voices, many=True)
        return redirect('audiobook:voice_custom_complete')

        # return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            # print(serializer.data, status.HTTP_201_CREATED)
            # return redirect('audiobook:voice_custom_complete')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
