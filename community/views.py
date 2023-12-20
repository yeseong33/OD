import requests
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import status
import os
from pathlib import Path
from dotenv import load_dotenv
from audiobook.models import Book
from user.models import User
from .models import BookRequest, UserRequestBook
from .serializers import *
from django.db import transaction
from django.db.models import F

load_dotenv()  # 환경 변수를 로드함

def book_share(request):
    return render(request, 'community/book_share.html')

class BookSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_search.html'

    def get(self, request):
        query = request.GET.get('query', '')
        display_count = 20 # 매개변수 (최대 100)
        context = {'books': None}

        if query:
            url = "https://openapi.naver.com/v1/search/book.json"
            headers = {
                "X-Naver-Client-Id": os.getenv('CLIENT_ID'),
                "X-Naver-Client-Secret": os.getenv('CLIENT_SECRET'),
            }
            params = {
                'query': query, 
                'display': display_count,  # 결과 수 조정
                }
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                context['books'] = response.json()['items']
            else:
                context['error'] = "An error occurred while searching for books."

        return Response(context)
    
    
class BookCompleteView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_complete.html'
    
    def get(self, request, isbn):
        
        ## 로그인 구현 전 커스텀 User 모델을 사용하여 임시 유저 생성
        # ttemp_user = User.objects.create(
        #     oauth_provider='some_provider',
        #     oauth_identifier='some_identifier',  # 필요에 따라 설정
        #     user_name='new_user_name',
        #     user_email='user@example.com',
        #     user_phone_number='000-0000-0000',
        #     user_book_history = [1, 2, 3], 
        #     user_favorite_books = [4, 5, 6],
        #     user_favorite_voices = [7, 8, 9],
        # )
        # ttemp_user.save()
        ttemp_user = User.objects.get(user_id=1)
        
        book_request, created = BookRequest.objects.get_or_create(request_isbn=isbn, defaults={'request_count': 0})
        
        # Atomically increment the request_count to ensure accuracy with concurrent requests
        with transaction.atomic():
            BookRequest.objects.filter(request_isbn=isbn).update(request_count=F('request_count') + 1)
            book_request.refresh_from_db()
        
        # if request.user.is_authenticated:
        #     UserRequestBook.objects.create(user=request.user, request=book_request)
        UserRequestBook.objects.create(user=ttemp_user, request=book_request)
        
        return Response(status=status.HTTP_200_OK)

def book_inquiry(request):
    return render(request, 'community/book_inquiry.html')

def book_faq(request):
    return render(request, 'community/book_faq.html')