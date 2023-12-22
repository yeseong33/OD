from django.shortcuts import render, redirect
from django.urls.base import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from .models import *
from dotenv import load_dotenv
import os
import requests
import bcrypt

load_dotenv() 

def index(request):
    return render(request, 'user/index.html')

def login(request):
    return render(request, 'user/login.html')

def kakao_login(request):
    print("kakao Login 클릭")
    return redirect(f"https://kauth.kakao.com/oauth/authorize?client_id={os.getenv('KAKAO_CLIENT_ID')}&redirect_uri={os.getenv('KAKAO_REDIRECT_URI')}&response_type=code")

def kakao_callback(request):
    
    #access_token 발급.
    code = request.GET.get('code')
    url = "https://kauth.kakao.com/oauth/token"
    headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv('KAKAO_CLIENT_ID'),
        "redirect_uri":  os.getenv('KAKAO_REDIRECT_URI'),
        "code": request.GET.get('code')
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = response.json().get('access_token')
    
    #access_token으로 유저 개인 정보 발급 받기.
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization" : f"Bearer {access_token}", "Content-type" : "application/x-www-form-urlencoded;charset=utf-8"}
    response = requests.post(url, headers=headers)
    user_inform = response.json().get('kakao_account')

    # name, email을 이용해 jwt token 발급
    jwt_token = sign_in(user_inform['profile']['nickname'],user_inform['email'], 'Kakao')
    
    return redirect('audiobook:main')

def google_login(request):
    print("google Login 클릭")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email")

def google_callback(request):
    
    #access_token 발급 받기
    url = "https://oauth2.googleapis.com/token"
    headers = {"Content-type" : "application/x-www-form-urlencoded"}
    data = {
        "grant_type" : "authorization_code",
        "client_id" : os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret" :  os.getenv('GOOGLE_SECRET_KEY'),
        "code" :request.GET.get('code'),
        "redirect_uri" : os.getenv('GOOGLE_REDIRECT_URI'),
    }
    response = requests.post(url, headers=headers, data=data)
    access_token  = response.json().get('access_token')
    
    # user_inform 받기.
    url  = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization" : f"Bearer {access_token}"}
    response =  requests.get(url = url, headers=headers)

    
    jwt_token = sign_in(response.json()['name'],response.json()['email'], 'Google') # name, email을 이용해 jwt token 발급
    return redirect('audiobook:main')

def sign_in(name, email, social_inform):
    print(f"sing in method name : {name}, email :{email}, social_inform : {social_inform}")
    
    if not User.objects.filter(user_name = name, user_email = email).exists():
        print("User Is Not Exists So create User")
        temp_password = email+os.getenv("USER_PASSWORD")
        new_user = User.objects.create(
                                        user_name=name, 
                                        user_email = email,
                                        user_password = bcrypt.hashpw(temp_password.encode("utf-8"),bcrypt.gensalt()).decode("utf-8"),
                                        oauth_provider = social_inform)
        new_user.save()
    
    
    return "hello"