import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
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

load_dotenv()  # 환경 변수를 로드함


def book_share(request):
    return render(request, 'community/book_share.html')

def book_share_content(request):
    return render(request, 'community/book_share_content.html')

def book_share_content_post(request):
    return render(request, 'community/book_share_content_post.html')

def book_share_content_comment(request):
    return render(request, 'community/book_share_content_comment.html')


class BookSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_search.html'

    def get(self, request):
        query = request.GET.get('query', '')
        display_count = 20  # 매개변수 (최대 100)
        context = {'books': None}

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


class BookCompleteView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_complete.html'

    def get(self, request, isbn):

        # 로그인 구현 전 커스텀 User 모델을 사용하여 임시 유저 생성
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

        book_request, created = BookRequest.objects.get_or_create(
            request_isbn=isbn, defaults={'request_count': 0})

        # Atomically increment the request_count to ensure accuracy with concurrent requests
        with transaction.atomic():
            BookRequest.objects.filter(request_isbn=isbn).update(
                request_count=F('request_count') + 1)
            book_request.refresh_from_db()

        # if request.user.is_authenticated:
        #     UserRequestBook.objects.create(user=request.user, request=book_request)
        UserRequestBook.objects.create(user=ttemp_user, request=book_request)

        return Response(status=status.HTTP_200_OK)


def book_inquiry(request):
    return render(request, 'community/book_inquiry.html')


def book_faq(request):
    return render(request, 'community/book_faq.html')

class BookShareContentList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share.html'
    
    def get(self, request):
        books = Book.objects.all()
        # Serializer를 사용하여 Book 데이터를 JSON으로 변환
        serializer = BookSerializer(books, many=True)
        return Response({'books': serializer.data}, template_name= self.template_name)
    

class BookShareContent(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_share_content.html'
    
    def get(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            print('book not exist.')
            return Response(status=404, template_name=self.template_name)
        posts = Post.objects.all()
        book_serializer = BookSerializer(book)
        posts_serializer = PostSerializer(posts, many=True)
        return Response({'book': book_serializer.data, 'posts': posts_serializer.data}, template_name= self.template_name)
    
    
class BookShareContentPost(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post.html'
    
    def get(self, request):
        return Response({'result': False, 'message': 'GET 요청은 허용되지 않습니다.'})

    def post(self, request):
        print(request.data)
        user_inform = jwt.decode(request.COOKIES.get("jwt"), key=os.getenv("JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")])
        user_id = user_inform['user_id']
        book_id = request.data['book_id']
        context={
            'book_id': book_id, 
            'user_id':user_id
        }
        # POST 요청에서 폼 데이터를 처리하고 게시물
        post_serializer = PostSerializer(data=request.data, context=context)
        if post_serializer.is_valid():
            post = post_serializer.save()
            # 책을 성공적으로 생성했을 때의 로직 추가 가능
            return Response({'result': True, 'post': post, 'message': '게시물이 성공적으로 생성되었습니다.'})
        else:
            # 폼 데이터가 유효하지 않을 때의 로직 추가 가능
            return Response({'result': False, 'errors': post_serializer.errors}, status=400, template_name=self.template_name)


    def put(self, request, post_id):
        print(request.data)
        new_title = request.data.get('new_title')
        new_content = request.data.get('new_content')
        try:
            self.update_post(post_id, new_title, new_content)
            redirect_url = reverse('community:book_share_content_post_detail', kwargs={'post_id': post_id})    
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
    

class BookShareContentPostDetail(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'community/book_share_content_post_detail.html'
    
    def get(self, request, post_id):
        # 수정: post에 맞게
        try:
            post = Post.objects.get(pk=post_id)
            comments = Comment.objects.filter(post__post_id=post_id)
        except Post.DoesNotExist:
            print('post not exist.')
            return Response(status=404, template_name=self.template_name)
        post_serializer = PostSerializer(post)
        comment_serializer = CommentSerializer(comments, many=True)
                
        if self.request.accepted_renderer.format == 'html':
            # HTML 요청인 경우에는 HTML 렌더링을 위한 데이터를 사용하여 템플릿을 렌더링합니다.
            # 이때, 게시글 데이터와 함께 템플릿을 렌더링
            context = {
                'post': post_serializer.data,
                'comments': comment_serializer.data,
            }
            return Response(context, template_name=self.template_name)
        # JSON 데이터를 Response로 반환
        return Response({'post': post_serializer.data}, template_name= self.template_name)
    
    def delete(self, request, post_id):
        post = get_object_or_404(Post, post_id=post_id)
        book_id = post.book.book_id
        post.delete()
        redirect_url = reverse('community:book_share_content', kwargs={'book_id': book_id})    
        return Response({'result': True, 'redirect_url': redirect_url})
    
    
    
class BookShareContentPostComment(APIView):
    renderer_classes = [JSONRenderer]
    template_name = 'community/book_share_content_post_detail.html'
    
    def get(self, request):
        return Response({'result': False, 'message': 'GET request not allow.'})
    
    def post(self, request):
        # POST 요청에서 폼 데이터를 처리하고 책을 생성
        comment_serializer = CommentSerializer(data=request.data, context={'post_id': request.data['post']})
        if comment_serializer.is_valid():
            comment = comment_serializer.save()  
            post_id = comment.post.post_id
            redirect_url = reverse('community:book_share_content_post_detail', kwargs={'post_id': post_id})    
            return Response({'result': True, 'comment': comment_serializer.data, 'message': 'comment created.', "redirect_url": redirect_url})
        else:
            # 폼 데이터가 유효하지 않을 때의 로직 추가 가능
            return Response({'result': False, 'errors': comment_serializer.errors}, status=400, template_name=self.template_name)
