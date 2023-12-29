import os
from dotenv import load_dotenv
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import VoiceSerializer
from .models import *
from user.views import decode_jwt
from config.settings import AWS_S3_CUSTOM_DOMAIN
from django.templatetags.static import static
from community.models import BookRequest
from django.db.models import Q

load_dotenv()


# 첫 화면

def index(request):
    if request.user.is_authenticated:  # 로그인 되어 있으면 main 페이지로 리다이렉트
        return redirect('audiobook:main')

    else:  # 로그인 되어 있지 않으면 index 페이지를 렌더링
        return render(request, 'audiobook/index.html')
    
def test(request):
    return render(request, 'audiobook/ddd.html')


# 메인화면

def convert_sample_voice(rvc_path):
    sample_voice_path = ''
    return sample_voice_path
    
class MainView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main.html'

    def get(self, request):
        # 이달의 TOP 10 책
        top_books = Book.objects.all().order_by('-book_likes')[:10]
        
        # 최근 이용한 책
        user_history_book = []  # 최신 이용한 책 순서로 보이기 위해서 filter를 사용하지 않고 리스트를 만들어서 사용
        for book_id in request.user.user_book_history:
            book = get_object_or_404(Book, book_id=book_id)
            user_history_book.append(book)
        
        # 이달의 TOP 10 음성
        top_voices = Voice.objects.all().order_by('-voice_like')[:10]
        # AI 기능 구현 이후
        # for voice in top_voices:
            # voice.voice_sample_path = convert_sample_voice(voice.voice_path) # 객체 속성(필드) 동적 추가
        # voice.voice_sample_path = static('voices/voice_sample.mp3')
        return Response({
            'top_books': top_books,
            'user_history_book': user_history_book,
            'top_voices': top_voices,
            'user': request.user,
            'AWS_S3_CUSTOM_DOMAIN': AWS_S3_CUSTOM_DOMAIN,
        })

class MainSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main_search.html'
    
    def get(self, request):
        query = request.query_params.get('query', '')
        book_list = Book.objects.filter( Q(book_title__icontains=query) | Q(book_author__icontains=query))        
        return Response({'book_list': book_list, 'AWS_S3_CUSTOM_DOMAIN': AWS_S3_CUSTOM_DOMAIN})
    
    
def genre(request):
    pass


def search(request):
    pass


# 청취
class Content(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/content.html'

    def get(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            print('book not exist.')
            return Response(status=404, template_name=self.template_name)
        context = {
            'result': True,
            'book': book,
        }
        return Response(context, template_name=self.template_name)
    
    
class ContentPlay(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/content_play.html'

    def get(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            print('book not exist.')
            return Response(status=404, template_name=self.template_name)
        context = {
            'result': True,
            'book': book,
        }
        return Response(context, template_name=self.template_name)

# 성우
def voice_custom(request):
    return render(request, 'audiobook/voice_custom.html')


def voice_celebrity(request):
    pass


def voice_custom_upload(request):
    return render(request, 'audiobook/voice_custom_upload.html')


def voice_custom_complete(request):
    return render(request, 'audiobook/voice_custom_complete.html')


def voice_custom_upload_post(request):
    return render(request, 'audiobook/voice_custom.html')


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
