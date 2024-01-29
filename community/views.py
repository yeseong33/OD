# 표준 라이브러리
import json
import os
import threading
from pathlib import Path
from datetime import datetime

# 서드 파티 라이브러리
import requests
from dotenv import load_dotenv
from jose import jwt

# Django 관련 라이브러리
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser

# Django REST framework 관련 라이브러리
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

# 현재 프로젝트의 다른 앱 모듈
from audiobook.models import Book
from user.models import User
from .models import BookRequest, Post, UserRequestBook
from manager.models import FAQ
from .serializers import *
from user.serializers import UserSerializer
from config.settings import AWS_S3_CUSTOM_DOMAIN, MEDIA_URL, FILE_SAVE_POINT
from manager.serializers import FAQSerializer
from user.views import decode_jwt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

load_dotenv()  # 환경 변수를 로드함


# 토론방
class BookShareHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request):
        file_path = self.get_file_path()
        books = Book.objects.all().order_by('book_id')
        user = request.user

        if isinstance(user, AnonymousUser):
            user_favorites = []
        else:
            user_favorites = user.user_favorite_books
            if user_favorites is None:
                user_favorites = []  # None으로 처리되면 template에서 인식하지 못하므로, 빈 값으로 처리

        print(user_favorites)

        # 검색어 처리
        search_term = request.GET.get('search_term')
        if search_term:
            books = books.filter(book_title__icontains=search_term)

        # 페이지네이터 설정
        paginator = Paginator(books, 12)  # 페이지당 12개의 아이템
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'file_path': file_path,
            'page_obj': page_obj,
            'user_favorites': user_favorites,
            'active_tab': 'book_share'
        }

        return Response(context, template_name=self.template_name)


# class BookLikeView(APIView):
#     renderer_classes = [TemplateHTMLRenderer]

#     def post(self, request):
#         user_inform = decode_jwt(request.COOKIES.get("jwt"))
#         user = User.objects.get(user_id=user_inform['user_id'])
#         book_id = int(request.data.get('book_id'))
#         book = Book.objects.get(book_id=book_id)

#         liked = False  # 사용자가 좋아요를 눌렀는지 여부

#         if user.user_favorite_books is None:
#             user.user_favorite_books = [book_id]
#             book.book_likes += 1
#             liked = True
#         else:
#             if book_id in user.user_favorite_books:
#                 user.user_favorite_books.remove(book_id)
#                 book.book_likes -= 1
#             else:
#                 user.user_favorite_books.append(book_id)
#                 book.book_likes += 1
#                 liked = True

#         user.save()
#         book.save()

#         return JsonResponse({'success': True, 'liked': liked, 'book_likes': book.book_likes})


@method_decorator(login_required(login_url="user:login"), name='dispatch')
class BookShareContentHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book_serializer = BookSerializer(book)
        serialized_json = json.dumps(
            book_serializer.data, ensure_ascii=False, indent=3)

        posts = book.post_set.all()
        paginator = Paginator(posts, 10)  # 한 페이지당 10개의 게시물
        page_number = request.GET.get('page', 1)  # URL에서 페이지 번호를 가져옴
        page_obj = paginator.get_page(page_number)

        context = {
            'book': book_serializer.data,
            'book_json': serialized_json,
            'page_obj': page_obj,
        }

        return Response(context, template_name=self.template_name)


class BookShareContentPostHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post.html'

    def get(self, request):
        return Response(template_name=self.template_name)


class BookShareContentPostDetailHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post_detail.html'

    def get_file_path(self):
        if FILE_SAVE_POINT == 'local':
            return MEDIA_URL
        else:
            return AWS_S3_CUSTOM_DOMAIN

    def get(self, request, pk):
        file_path = self.get_file_path()

        try:
            post = Post.objects.get(pk=pk)
            comments = Comment.objects.filter(post__post_id=pk)
        except Post.DoesNotExist:
            print('post not exist.')
            return Response(status=404, template_name=self.template_name)
        post_serializer = PostSerializer(post)
        comment_serializer = CommentSerializer(comments, many=True)
        context = {
            'file_path': file_path,
            'post': post_serializer.data,
            'comments': comment_serializer.data,
            'user_id': request.user.user_id,
        }

        print(comments)
        return Response(context, template_name=self.template_name)


# 신규 도서 신청 페이지
class BookSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_search.html'

    def get(self, request):
        query = request.GET.get('query', '')
        display_count = 20  # 매개변수 (최대 100)
        context = {
            'books': None,
            'active_tab': 'book_search'
        }

        if query:
            url = "https://openapi.naver.com/v1/search/book.json"
            headers = {
                "X-Naver-Client-Id": os.getenv('NAVER_CLIENT_ID'),
                "X-Naver-Client-Secret": os.getenv('NAVER_CLIENT_SECRET'),
            }
            params = {
                'query': query,
                'display': display_count,  # 결과 수 조정
            }
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                api_books = response.json()['items']

                # Book 테이블에 없는 책들만 필터링
                existing_isbns = set(
                    Book.objects.values_list('book_isbn', flat=True))
                filtered_books = [
                    book for book in api_books if book['isbn'] not in existing_isbns]
                context['books'] = filtered_books

            else:
                context['error'] = "An error occurred while searching for books."
            # print(context['books'])
        return Response(context)

# 신규 도서 신청 완료 페이지
class EmailThread(threading.Thread):  # threading 모듈을 사용하여 이메일 전송을 별도의 스레드에서 실행
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_async_mail(subject, message, from_email, recipient_list):  # 이메일 전송을 별도의 스레드에서 처리
    email = EmailMessage(
        subject, message,  from_email=from_email, to=recipient_list)
    EmailThread(email).start()


@method_decorator(login_required(login_url="user:login"), name='dispatch')
class BookRequestAPI(APIView):
    def get(self, request, isbn):
        context = {
            'active_tab': 'book_search'
        }

        book_request, created = BookRequest.objects.get_or_create(
            request_isbn=isbn, defaults={'request_count': 0})

        existing_user_request = UserRequestBook.objects.filter(
            user_id=request.user.user_id, request=book_request).exists()
        if existing_user_request:
            context['message'] = "이미 신청한 책입니다. 등록이 완료되면 메일로 알려드리겠습니다."
        else:
            # Atomically increment the request_count to ensure accuracy with concurrent requests
            with transaction.atomic():
                BookRequest.objects.filter(request_isbn=isbn).update(
                    request_count=F('request_count') + 1)
                book_request.refresh_from_db()

            UserRequestBook.objects.create(
                user=request.user, request=book_request)
            context['message'] = '신규 도서 신청이 완료되었습니다. 등록이 완료되면 메일로 알려드리겠습니다.'

        # 이메일 보내기
        if request.user.email:
            try:
                subject = '[오디 알림] 책 신청 완료'
                html_content = render_to_string(
                    'community/email_template.html', {'nickname': request.user.nickname})
                plain_message = strip_tags(html_content)
                from_email = '오디 <wooyoung9654@gmail.com>'
                send_async_mail(subject, plain_message,
                                from_email, [request.user.email])
                print('Email sent successfully')
            except Exception as e:
                # 로그 기록, 오류 처리 등
                print(f'Error sending email: {e}')

        return Response(context)

# 1:1 문의


@method_decorator(login_required(login_url='user:login'), name='dispatch')
class InquiryPostHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_inquiry.html'

    def get(self, request):
        print(request.user)
        context = {
            "user": request.user,
            'active_tab': 'book_inquiry'
        }
        return Response(context, template_name=self.template_name)


class InquiryPostCompleteHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_inquiry_complete.html'

    def get(self, request):
        print(request.user)
        context = {
            "user": request.user,
            "result": True,
            'active_tab': 'book_inquiry'
        }
        return Response(context, template_name=self.template_name)


# FAQ
class FAQHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_faq.html'

    def get(self, request):
        faqs = FAQ.objects.all()
        serializers = FAQSerializer(faqs, many=True)
        context = {
            'active_tab': 'book_faq',
            'faqs': serializers.data,
        }
        return Response(context, template_name=self.template_name)