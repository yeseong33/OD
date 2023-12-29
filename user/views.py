import os
from dotenv import load_dotenv
import requests
from datetime import timedelta, datetime
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from jose import jwt
import bcrypt
from .models import *
from audiobook.models import *

load_dotenv()


def index(request):
    return render(request, 'user/index.html')


def login(request):
    return render(request, 'user/login.html')


def logout(request):
    response = redirect('audiobook:index')  # 첫 화면으로 리다이렉트
    response.delete_cookie('jwt')
    return response


def kakao_login(request):
    print("kakao Login 클릭")
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI_PRODUCTION')
        print('in production')

    return redirect(f"https://kauth.kakao.com/oauth/authorize?client_id={os.getenv('KAKAO_CLIENT_ID')}&redirect_uri={redirect_uri}&response_type=code")


def kakao_callback(request):
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI_PRODUCTION')
        print('in production')

    # access_token 발급
    code = request.GET.get('code')
    url = "https://kauth.kakao.com/oauth/token"
    headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv('KAKAO_CLIENT_ID'),
        "redirect_uri":  redirect_uri,
        "code": request.GET.get('code')
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = response.json().get('access_token')

    # access_token으로 유저 개인 정보 발급 받기
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}",
               "Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
    response = requests.post(url, headers=headers)
    user_inform = response.json().get('kakao_account')

    # name, email을 이용해 jwt token 발급, main 페이지로 전달
    user = sign_in(user_inform['profile']['nickname'],
                   user_inform['email'],
                   response.json().get('properties')['thumbnail_image'],
                   'Kakao')
    token = get_jwt_token(user)
    response = redirect("audiobook:main")
    response.set_cookie("jwt", token)
    return response


def google_login(request):
    print("google Login 클릭")
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI_PRODUCTION')
        print('in production')

    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={redirect_uri}&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email")


def google_callback(request):
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    else:
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI_PRODUCTION')

    # access_token 발급 받기
    url = "https://oauth2.googleapis.com/token"
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret":  os.getenv('GOOGLE_SECRET_KEY'),
        "code": request.GET.get('code'),
        "redirect_uri": redirect_uri,
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = response.json().get('access_token')

    # user_inform 받기
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url=url, headers=headers)

    # user DB조회, JWT 발급
    user = sign_in(response.json()['name'],
                   response.json()['email'],
                   response.json()['picture'],
                   'Google')
    token = get_jwt_token(user)
    response = redirect("audiobook:main")
    response.set_cookie("jwt", token)
    return response

# 사용자 정보를 DB에서 조회


def sign_in(nickname, email, user_profile_path, social_inform):
    print(
        f"sign_in 시작: {nickname}, email :{email}, social_inform : {social_inform}")

    if not User.objects.filter(username=email).exists():
        print("User is not exists. So, User is created.")
        temp_password = email+os.getenv("USER_PASSWORD")
        user = User.objects.create_user(
            email=email,
            nickname=nickname,
            oauth_provider=social_inform,
            user_profile_path=user_profile_path,)
        user.save()
    else:
        user = User.objects.get(username=email)
    return user

# 사용자 정보를 바탕으로 JWT 토큰 발급


def get_jwt_token(user):
    print(f"create jwt 메소드 진입.")
    payload = {"user_id": user.user_id, "user_email": user.email,
               "exp": datetime.utcnow() + timedelta(hours=24)}
    secret_key = os.getenv("JWT_SECRET_KEY")
    token = jwt.encode(payload, secret_key,
                       algorithm=os.getenv("JWT_ALGORITHM"))

    print(f"JWT token 생성 완료 : {token}")
    decode_jwt(token)
    return token

# JWT 복호화


def decode_jwt(token):
    user_inform = jwt.decode(token, key=os.getenv(
        "JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")])
    return user_inform


class UserSubscriptionView(APIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        if request.COOKIES.get("jwt") == None:  # User가 로그인 안했을 시
            print(f"user가 로그인하지 않고 Subscribe 페이지 접속.")
            return redirect('user:login')
        else:
            user_inform = decode_jwt(request.COOKIES.get("jwt"))
            user = User.objects.get(user_id=user_inform['user_id'])
            context = {
                'user': user,
                'active_tab': 'user_subscription',
                'is_subscribed': False,  # 구독 여부
                'left_days': 0  # 남은 일수. 기본값은 0.
            }

            try:
                subscribe = Subscription.objects.get(user_id=user.user_id)
                context['is_subscribed'] = True
                context['left_days'] = (
                    subscribe.sub_end_date - timezone.now()).days
            except Subscription.DoesNotExist:
                pass  # 구독 정보가 없으면 context['is_subscribed']는 False로 유지됨

            template_name = 'user/subscription.html'
            return Response(context, template_name=template_name)


class UserInformationView(APIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        template_name = 'user/information.html'
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        context = {
            'user': user,
            'active_tab': 'user_information'
        }
        return Response(context, template_name=template_name)

    def post(self, request):

        # cookie에 저장된 jwt 정보를 이용해 유저 받아오기
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])

        user_image = request.FILES.get('file')
        nickname = request.POST.get('nickname')
        # 사진 저장 로직 구현 필요. 보류 아마존 s3 버킷에 이미지를 저장.
        if nickname:
            user.nickname = nickname
        user.save()
        return redirect('user:information')


class UserLikeBooksView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/like_books.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        book_id_list = user.user_favorite_books
        context = {
            'active_tab': 'user_like'
        }

        if book_id_list == None:  # 유저가 좋아요한 목록이 없을 경우.
            context['books'] = None
        else:
            books = Book.objects.filter(pk__in=book_id_list)
            context['books'] = books
        return render(request, self.template_name, context)


class UserLikeVoicesView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/like_voices.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        voice_id_list = user.user_favorite_voices

        if voice_id_list == None:
            context = {'voices': None}
        else:
            voices = Voice.objects.filter(pk__in=voice_id_list)
            context = {'voices': voices}
        return render(request, self.template_name, context)


class UserBookHistoryView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/book_history.html'

    def get(self, request):
        context = {
            'active_tab': 'user_book_history'
        }

        return Response(context)


class UserFAQView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/faq.html'

    def get(self, request):
        context = {
            'active_tab': 'user_faq'
        }

        return Response(context)
