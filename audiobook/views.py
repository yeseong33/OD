import os
import time
import socket

import requests
import paramiko
import pygame
from dotenv import load_dotenv, dotenv_values

from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.templatetags.static import static

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.decorators import api_view
from rest_framework import status

from .serializers import VoiceSerializer
from .models import *
from user.views import decode_jwt
from community.models import BookRequest
from config.settings import AWS_S3_CUSTOM_DOMAIN, MEDIA_URL, FILE_SAVE_POINT

load_dotenv()

def play_wav(file_path):
    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(file_path)
    sound.play()

    # 소리 재생이 끝날 때까지 기다립니다
    while pygame.mixer.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.quit()
    pygame.quit()

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

    # 데이터 저장 위치를 .env의 FILE_SAVE_POINT에 따라 결정
    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request):
        # 이달의 TOP 10 책
        top_books = Book.objects.all().order_by('-book_likes')[:10]

        # 최근 이용한 책
        user_history_book = []  # 최신 이용한 책 순서로 보이기 위해서 filter를 사용하지 않고 리스트를 만들어서 사용
        if request.user.user_book_history is not None:
            for book_id in request.user.user_book_history:
                book = get_object_or_404(Book, book_id=book_id)
                user_history_book.append(book)

        # 이달의 TOP 10 음성
        top_voices = Voice.objects.all().order_by('-voice_like')[:10]
        # AI 기능 구현 이후
        # for voice in top_voices:
        # voice.voice_sample_path = convert_sample_voice(voice.voice_path) # 객체 속성(필드) 동적 추가
        # voice.voice_sample_path = static('voices/voice_sample.mp3')

        context = {
            'top_books': top_books,
            'user_history_book': user_history_book,
            'top_voices': top_voices,
            'user': request.user,
            'file_path': self.get_file_path(),
        }

        return Response(context)


class MainSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main_search.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request):
        query = request.query_params.get('query', '')
        book_list = Book.objects.filter(
            Q(book_title__icontains=query) | Q(book_author__icontains=query))

        file_path = self.get_file_path()
        for book in book_list:
            book.book_image_path = f"{file_path}{book.book_image_path}"

        context = {
            'book_list': book_list,
            'file_path': file_path
        }

        return Response(context)


class MainGenreView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main_genre.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request):
        file_path = self.get_file_path()

        categories = {
            '소설': Book.objects.filter(book_genre='novel').order_by('-book_likes')[:10],
            '인문': Book.objects.filter(book_genre='humanities').order_by('-book_likes')[:10],
            '자연과학': Book.objects.filter(book_genre='nature').order_by('-book_likes')[:10],
            '자기계발': Book.objects.filter(book_genre='self_improvement').order_by('-book_likes')[:10],
            '아동': Book.objects.filter(book_genre='children').order_by('-book_likes')[:10],
            '기타': Book.objects.filter(book_genre='etc').order_by('-book_likes')[:10],
        }

        context = {
            'file_path': file_path,
            'categories': categories,
        }

        return Response(context)

# RvcTrain
class RvcTrain(APIView):
    renderer_classes = [JSONRenderer,TemplateHTMLRenderer]
    template_name = 'audiobook/voice_custom_complete.html'

    def get(self, request):
        return Response({'result': False, 'message': 'GET 요청은 허용되지 않습니다.'})

    def post(self, request):
        print(request.data)

        config = dotenv_values(".env")
        hostname = config.get("RVC_IP")
        username = config.get("RVC_USER")
        key_filename = config.get("RVC_KEY")  # 개인 키 파일 경로

        voice_file = request.FILES['voice_file']
        voice_name = request.POST['voice_name']

        # SSH 클라이언트 생성
        client = paramiko.SSHClient()
        # 호스트 키 자동으로 수락
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # SSH 연결 (키 기반 인증)
        client.connect(hostname=hostname, username=username, key_filename=key_filename)

        # 셸 세션 열기
        shell = client.invoke_shell()

        def receive_until_prompt(shell, prompt='your_prompt', timeout=30):
            # prompt 문자열이 나타날 때까지 출력을 읽습니다.
            # timeout은 출력이 끝나기를 최대 몇 초간 기다릴지를 정합니다.
            buffer = ''
            shell.settimeout(timeout)  # recv 메소드에 타임아웃을 설정합니다.
            try:
                while not buffer.endswith(prompt):
                    response = shell.recv(1024).decode('utf-8',errors='replace')
                    buffer += response
            except socket.timeout:
                print("No data received before timeout")
            return buffer

        commands = [
            'ls\n',
            'cd project-main\n',
            'rm -rf voices\n',
            'mkdir voices\n',
            'cd assets\n',
            'rm -rf weights\n',
            'mkdir weights\n',
            'cd ..\n',
        ]

        for cmd in commands:
            shell.send(cmd)
            output = receive_until_prompt(shell, prompt='$ ')  # 각 명령의 실행이 끝날 때까지 기다립니다.
            print(output)  # 받은 출력을 표시합니다.

        # SFTP 클라이언트 시작
        sftp_client = client.open_sftp()

        # 임시 저장한 로컬 파일을 원격 시스템으로 업로드
        remote_path = '/home/kimyea0454/project-main/voices/' + voice_name + '.mp3'
        sftp_client.putfo(voice_file, remote_path)
        # SFTP 세션 종료
        sftp_client.close()

        commands = [
            'python3 preprocess.py '+voice_name+'\n',
            'python3 extract_features.py '+voice_name+'\n',
            'python3 train_index.py '+voice_name+'\n',
            'python3 train_model.py '+voice_name+'\n',
        ]

        for cmd in commands:
            shell.send(cmd)
            output = receive_until_prompt(shell, prompt='$ ')  # 각 명령의 실행이 끝날 때까지 기다립니다.
            print(output)  # 받은 출력을 표시합니다.

        # 연결 종료
        client.close()

        return Response(template_name=self.template_name)
    
# TTS
@api_view(["POST"])
def TTS(request):
    config = dotenv_values(".env")
    hostname = config.get("RVC_IP")
    username = config.get("RVC_USER")
    key_filename = config.get("RVC_KEY")  # 개인 키 파일 경로

    tone = request.POST['tone']
    text = request.POST['text']

    # SSH 클라이언트 생성
    client = paramiko.SSHClient()
    # 호스트 키 자동으로 수락
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # SSH 연결 (키 기반 인증)
    client.connect(hostname=hostname, username=username, key_filename=key_filename)

    # 셸 세션 열기
    shell = client.invoke_shell()

    def receive_until_prompt(shell, prompt='your_prompt', timeout=30):
        # prompt 문자열이 나타날 때까지 출력을 읽습니다.
        # timeout은 출력이 끝나기를 최대 몇 초간 기다릴지를 정합니다.
        buffer = ''
        shell.settimeout(timeout)  # recv 메소드에 타임아웃을 설정합니다.
        try:
            while not buffer.endswith(prompt):
                response = shell.recv(1024).decode('utf-8',errors='replace')
                buffer += response
        except socket.timeout:
            print("No data received before timeout")
        return buffer

    commands = [
        f'python3 tts.py {text}\n',
        'cd project-main\n',
        f'python3 inference.py IU {tone} audios/tts.mp3\n',
        'rm -rf audios/tts.mp3\n',
    ]

    try:
        for cmd in commands:
            shell.send(cmd)
            output = receive_until_prompt(shell, prompt='$ ')  # 각 명령의 실행이 끝날 때까지 기다립니다.
            print(output)  # 받은 출력을 표시합니다.
        
        sftp_client = client.open_sftp()

        # 임시 저장한 로컬 파일을 원격 시스템으로 업로드
        remote_path = '/home/kimyea0454/project-main/audios/' + 'IU' + '.wav'
        project_path = os.getcwd()
        sftp_client.get(remote_path, os.path.join(project_path, 'static/tts/IU.mp3'))
        # SFTP 세션 종료
        sftp_client.close()

        wav_file_path = os.path.join(project_path, 'static/tts/IU.mp3')
        play_wav(wav_file_path)
        
        return Response("Well funciotned", status=status.HTTP_200_OK)
    except:
        return Response("WRONG", status=status.HTTP_400_BAD_REQUEST)

def genre(request):
    pass


def search(request):
    pass


# 청취
class Content(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/content.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request, book_id):
        file_path = self.get_file_path()

        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            print('book not exist.')
            return Response(status=404, template_name=self.template_name)
        context = {
            'result': True,
            'book': book,
            'file_path': file_path
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

# 개인정보처리
def privacy_policy(request):
    return render(request, 'audiobook/privacy_policy.html')

