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
from django.shortcuts import redirect

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from jose import jwt
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
from django.http import Http404
import json

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


# book
class BookShareHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share.html'
    
    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        books = json.dumps(serializer.data)
        return Response({'books': books}, template_name=self.template_name)
    
class BookShareContentHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content.html'
    
    def get(self, request, pk):
        book = get_object_or_404(Book,pk=pk)
        serializer = BookSerializer(book)
        return Response({'book': serializer.data}, template_name=self.template_name)

class BookShareContentPostHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post.html'

    def get(self, request):
        return Response(template_name=self.template_name)
    
class BookShareContentPostDetailHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post_detail.html'

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            comments = Comment.objects.filter(post__post_id=pk)
        except Post.DoesNotExist:
            print('post not exist.')
            return Response(status=404, template_name=self.template_name)
        post_serializer = PostSerializer(post)
        comment_serializer = CommentSerializer(comments, many=True)
        context = {
            'post': post_serializer.data,
            'comments': comment_serializer.data,
        }
        return Response(context, template_name=self.template_name)



class BookList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response({"books": books})
    

    def post(self, request):
        book_serializer = BookSerializer(request.data)
        
        if book_serializer.is_valid():
            book_serializer.save()
            return Response(book_serializer.data, status=status.HTTP_201_CREATED)
        return Response(book_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookDetail(APIView):
    renderer_classes = [JSONRenderer]


    def get_object(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        book = self.get_object(pk)
        serializer = BookSerializer(book)
        return Response({"book": serializer.data})

    def put(self, request, pk, format=None):
        book = self.get_object(pk)
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        book = self.get_object(pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
# post
class PostList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        posts = Post.objects.all()
        serializer = BookSerializer(posts, many=True)
        return Response({"books": serializer.data})

    def post(self, request):
        print('pas')
        user_id = request.user.user_id
        book_id = request.data['book_id']
        context={
            'book_id': book_id, 
            'user_id':user_id
        }
        serializer = PostSerializer(data=request.data, context=context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PostDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post)
        print(serializer.data)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        print(request.data)
        new_title = request.data.get('new_title')
        new_content = request.data.get('new_content')
        try:
            self.update_post(pk , new_title, new_content)
            redirect_url = reverse('community:book_share_content_post_detail', kwargs={'pk': pk})    
            response_data = {'result': True, 'message': '게시물 내용이 업데이트되었습니다.', 'redirect_url': redirect_url}
        except Post.DoesNotExist:
            response_data = {'result': False, 'message': '게시물이 존재하지 않습니다.'}
        except Exception as e:
            response_data = {'result': False, 'message': str(e)}
        return Response(response_data)
    
    def update_post(self, post_id, new_title, new_content):
        post = get_object_or_404(Post, pk=post_id)
        post.post_title = new_title
        post.post_content = new_content
        post.save()

    def delete(self, request, pk, format=None):
        post = get_object_or_404(Post, pk=pk)
        book_id = post.book.book_id
        post.delete()
        redirect_url = reverse('community:book_share_content', kwargs={'pk': book_id})    
        return Response({'result': True, 'redirect_url': redirect_url})
        
    
# comment
class CommentList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        comments = Comment.objects.all()
        serializer = BookSerializer(comments, many=True)
        return Response({"books": serializer.data})

    def post(self, request):
        comment_serializer = CommentSerializer(data=request.data, context={
                                            'post_id': request.data['post']})
        if comment_serializer.is_valid():
            comment = comment_serializer.save()  
            post_id = comment.post.post_id
            redirect_url = reverse('community:book_share_content_post_detail', kwargs={'pk': post_id})    
            return Response({'result': True, 'comment': comment_serializer.data, 'message': 'comment created.', "redirect_url": redirect_url})
        return Response({'result': False, 'errors': comment_serializer.errors}, status=400)
    

class CommentDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get_object(self, pk):
        try:
            return Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        comment = self.get_object(pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        comment = self.get_object(pk)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        comment = self.get_object(pk)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


## 신규 도서 신청 기능

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
class EmailThread(threading.Thread): # threading 모듈을 사용하여 이메일 전송을 별도의 스레드에서 실행
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

def send_async_mail(subject, message, from_email, recipient_list): # 이메일 전송을 별도의 스레드에서 처리
    email = EmailMessage(subject, message,  from_email=from_email, to=recipient_list)
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

            UserRequestBook.objects.create(user=request.user, request=book_request)
            
            context['message'] = '<br>신청이 완료되었습니다.<br>등록이 완료되면 메일로 알려드리겠습니다.'
            context['image'] = static('images/complete_book.png') 
            
            # 이메일 보내기
            if request.user.email:
                try:
                    subject = '[오디 알림] 책 신청 완료'
                    html_content = render_to_string('community/email_template.html', {'nickname': request.user.nickname})
                    plain_message = strip_tags(html_content)
                    from_email = '오디 <wooyoung9654@gmail.com>' 
                    send_async_mail(subject, plain_message, from_email, [request.user.email])
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
