# 표준 라이브러리
from datetime import datetime

# 서드 파티 라이브러리
from dotenv import load_dotenv

# Django REST framework 관련 라이브러리
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Django 관련 라이브러리
from django.shortcuts import get_object_or_404
from django.urls import reverse

# 현재 프로젝트의 다른 앱 모듈
from user.models import User
from audiobook.models import Book
from community.models import Post, Comment, Inquiry
from manager.models import FAQ
from community.serializers import BookSerializer, PostSerializer, CommentSerializer, InquirySerializer
from user.serializers import UserSerializer
from manager.serializers import FAQSerializer
from user.views import decode_jwt

load_dotenv()  # 환경 변수를 로드함



# Create your views here.
class UserList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        users = User.objects.all()
        serializer = BookSerializer(users, many=True)
        return Response({"users": serializer.data})

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': True, 'users': serializer.data, 'message': 'users created.'})
        return Response({'result': False, 'errors': serializer.errors}, status=400)


class UserDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        print(serializer.data)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
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
    
    def get(self, request, pk, format=None):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookSerializer(book)
        return Response({"book": serializer.data})

    def put(self, request, pk, format=None):
        book = get_object_or_404(Book, pk=pk)
        print(request.data)
        # 현재 시간의 달 추출
        current_month = datetime.now().month
        context = {
            "month": current_month
        }
        serializer = BookSerializer(
            book, context=context, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'book': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        book = get_object_or_404(Book, pk=pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookLikeView(APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        book_id = int(request.data.get('book_id'))
        book = Book.objects.get(book_id=book_id)

        liked = False  # 사용자가 좋아요를 눌렀는지 여부

        if user.user_favorite_books is None:
            user.user_favorite_books = [book_id]
            book.book_likes += 1
            liked = True
        else:
            if book_id in user.user_favorite_books:
                user.user_favorite_books.remove(book_id)
                book.book_likes -= 1
            else:
                user.user_favorite_books.append(book_id)
                book.book_likes += 1
                liked = True

        user.save()
        book.save()

        return Response({'success': True, 'liked': liked, 'book_likes': book.book_likes})


# post
class PostList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        posts = Post.objects.all()
        serializer = BookSerializer(posts, many=True)
        return Response({"books": serializer.data})

    def post(self, request):
        user_id = request.user.user_id
        book_id = request.data['book_id']
        context = {
            'book_id': book_id,
            'user_id': user_id
        }
        print(user_id)
        print(book_id)

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
            self.update_post(pk, new_title, new_content)
            redirect_url = reverse(
                'community:book_share_content_post_detail', kwargs={'pk': pk})
            response_data = {
                'result': True, 'message': '게시물 내용이 업데이트되었습니다.', 'redirect_url': redirect_url}
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
        redirect_url = reverse(
            'community:book_share_content', kwargs={'pk': book_id})
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
            'post_id': request.data['post'],
            'user_id': request.user.user_id, })
        if comment_serializer.is_valid():
            comment = comment_serializer.save()
            post_id = comment.post.post_id
            redirect_url = reverse(
                'community:book_share_content_post_detail', kwargs={'pk': post_id})
            return Response({'result': True, 'comment': comment_serializer.data, 'message': 'comment created.', "redirect_url": redirect_url})
        return Response({'result': False, 'errors': comment_serializer.errors}, status=400)


class CommentDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        comment = get_object_or_404(Comment, pk=pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        comment = get_object_or_404(Comment, pk=pk)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        comment = get_object_or_404(Comment, pk=pk)
        post_id = comment.post.post_id
        comment.delete()
        redirect_url = reverse(
            'community:book_share_content_post_detail', kwargs={'pk': post_id})
        return Response({'result': True, 'redirect_url': redirect_url})

class InquiryList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        inquirys = Inquiry.objects.all()
        serializer = InquirySerializer(inquirys, many=True)
        return Response({"inquirys": serializer.data})

    def post(self, request):
        serializer = InquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': True, 'inquirys': serializer.data, 'message': 'inquirys created.'})
        return Response({'result': False, 'errors': serializer.errors}, status=400)


class InquiryDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        serializer = InquirySerializer(inquiry)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        serializer = InquirySerializer(inquiry, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        inquiry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class FAQList(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        faqs = FAQ.objects.all()
        serializer = BookSerializer(faqs, many=True)
        return Response({"faqs": serializer.data})

    def post(self, request):
        serializer = FAQSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': True, 'faqs': serializer.data, 'message': 'users created.'})
        return Response({'result': False, 'errors': serializer.errors}, status=400)


class FAQDetail(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        faq = get_object_or_404(FAQ, pk=pk)
        serializer = FAQSerializer(faq)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        faq = get_object_or_404(FAQ, pk=pk)
        serializer = FAQSerializer(faq, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        faq = get_object_or_404(FAQ, pk=pk)
        faq.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)