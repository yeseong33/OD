import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from audiobook.models import Book
from .models import Post
from user.models import User
from .models import BookRequest, UserRequestBook
from .serializers import *
from django.db import transaction
from django.db.models import F
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading

load_dotenv()  # 환경 변수를 로드함

# 토론방


def book_share(request):
    return render(request, 'community/book_share.html')


def book_share_content(request):
    return render(request, 'community/book_share_content.html')


def book_share_content_post(request):
    return render(request, 'community/book_share_content_post.html')


def book_share_content_comment(request):
    return render(request, 'community/book_share_content_comment.html')


class BookShareContentList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share.html'

    def get(self, request):
        books = Book.objects.all()
        # Serializer를 사용하여 Book 데이터를 JSON으로 변환
        serializer = BookSerializer(books, many=True)

        context = {
            'books': serializer.data,
            'active_tab': 'book_share'
        }
        return Response(context, template_name=self.template_name)


class BookShareContent(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content.html'

    def get(self, request, book_id):
        book_id = 1
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            print('책이 존재하지 않습니다.')
            return Response(status=404, template_name=self.template_name)
        posts = Post.objects.all()
        book_serializer = BookSerializer(book)
        posts_serializer = PostSerializer(posts, many=True)

        return Response({'book': book_serializer.data, 'posts': posts_serializer.data}, template_name=self.template_name)


class BookShareContentPost(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post.html'

    def get(self, request):
        return Response({'result': False, 'message': 'GET 요청은 허용되지 않습니다.'})

    def post(self, request):
        print(request.data)
        # POST 요청에서 폼 데이터를 처리하고 게시물
        post_serializer = PostSerializer(
            data=request.data, context={'request': request})
        if post_serializer.is_valid():
            post = post_serializer.save()
            # 책을 성공적으로 생성했을 때의 로직 추가 가능
            return Response({'result': True, 'post': post, 'message': '게시물이 성공적으로 생성되었습니다.'})
        else:
            # 폼 데이터가 유효하지 않을 때의 로직 추가 가능
            return Response({'result': False, 'errors': post_serializer.errors}, status=400, template_name=self.template_name)


class BookShareContentPostDetail(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post_detail.html'

    def get(self, request, post_id):
        # 수정: post에 맞게
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            print('게시글이 존재하지 않습니다.')
            return Response(status=404, template_name=self.template_name)
        post_serializer = PostSerializer(post)
        if self.request.accepted_renderer.format == 'html':
            # HTML 요청인 경우에는 HTML 렌더링을 위한 데이터를 사용하여 템플릿을 렌더링합니다.
            # 이때, 게시글 데이터와 함께 템플릿을 렌더링
            context = {'post': post_serializer.data}  # html에 사용할 data
            return Response(context, template_name=self.template_name)

        # JSON 데이터를 Response로 반환
        return Response({'post': post_serializer.data}, template_name=self.template_name)


class BookShareContentPostComment(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post_detail.html'

    def get(self, request):
        return Response({'result': False, 'message': 'GET 요청은 허용되지 않습니다.'})

    def post(self, request):
        # POST 요청에서 폼 데이터를 처리하고 책을 생성
        comment_serializer = CommentSerializer(data=request.data, context={
                                               'post_id': request.data['post']})
        if comment_serializer.is_valid():
            post = comment_serializer.save()
            return Response({'result': True, 'comment': comment_serializer.data, 'message': '게시물이 성공적으로 생성되었습니다.'})
        else:
            # 폼 데이터가 유효하지 않을 때의 로직 추가 가능
            return Response({'result': False, 'errors': comment_serializer.errors}, status=400, template_name=self.template_name)


# 신규 도서 신청 기능

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
                context['books'] = response.json()['items']
            else:
                context['error'] = "An error occurred while searching for books."

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


class BookCompleteView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_complete.html'

    def get(self, request, isbn):
        context = {}
        if Book.objects.filter(book_isbn=isbn).exists():
            context['message'] = '<br>이미 등록되어 사용 가능한 책입니다.'
            context['image'] = static('images/exist.png')
            return Response(context)

        else:
            book_request, created = BookRequest.objects.get_or_create(
                request_isbn=isbn, defaults={'request_count': 0})

            # Atomically increment the request_count to ensure accuracy with concurrent requests
            with transaction.atomic():
                BookRequest.objects.filter(request_isbn=isbn).update(
                    request_count=F('request_count') + 1)
                book_request.refresh_from_db()

            UserRequestBook.objects.create(
                user=request.user, request=book_request)

            context['message'] = '<br>신청이 완료되었습니다.<br>등록이 완료되면 메일로 알려드리겠습니다.'
            context['image'] = static('images/complete_book.png')

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


def book_inquiry(request):
    context = {'active_tab': 'book_inquiry'}
    return render(request, 'community/book_inquiry.html', context)

# FAQ


def book_faq(request):
    context = {'active_tab': 'book_faq'}
    return render(request, 'community/book_faq.html', context)


# 개인정보처리
def privacy_policy(request):
    return render(request, 'community/privacy_policy.html')
