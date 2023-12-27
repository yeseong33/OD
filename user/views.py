import os
from dotenv import load_dotenv
import requests
import bcrypt
from jose import jwt
from datetime import timedelta, datetime
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls.base import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from .models import *
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer


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
                    response.json()['picture'] ,
                    'Google')
    token = get_jwt_token(user)
    response = redirect("audiobook:main")
    response.set_cookie("jwt", token)
    return response

# 사용자 정보를 DB에서 조회


def sign_in(nickname, email, user_profile_path ,social_inform):
    print(
        f"sign_in 시작: {nickname}, email :{email}, social_inform : {social_inform}")

    if not User.objects.filter(username = email).exists():
        print("User is not exists. So, User is created.")
        temp_password = email+os.getenv("USER_PASSWORD")
        user = User.objects.create_user(
            email = email,
            nickname = nickname,
            oauth_provider = social_inform,
            user_profile_path = user_profile_path,)
        user.save()
    else:
        user = User.objects.get(username = email)
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

class SubscribeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    def get(self, request):
        if request.COOKIES.get("jwt") == None: # User가 로그인 안했을시.
            print(f"user가 로그인하지 않고 Subscribe 페이지 접속.")
            return redirect('user:login')
        else:
            user_inform = decode_jwt(request.COOKIES.get("jwt"))
            user = User.objects.get(user_id=user_inform['user_id'])
            is_subscribe = user.is_subscribe
            if is_subscribe:
                print(f"{user.nickname} : {user.is_subscribe}")
                template_name = 'user/pay_inform.html'
                return Response({'user' : user}, template_name=template_name)
            else:
                print(f"{user.nickname} : {user.is_subscribe}")
                template_name = 'user/non_pay_inform.html'
                return Response(template_name=template_name)