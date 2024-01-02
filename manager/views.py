from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.files.base import ContentFile
from community.models import BookRequest, UserRequestBook
from .serializers import BookSerializer
from audiobook.models import Book
from user.models import User
import requests
from django.shortcuts import render, get_object_or_404
from dotenv import load_dotenv
import datetime
import os

load_dotenv()  # 환경 변수를 로드함

## 도서 신청 확인 페이지
def get_book_details_from_naver(isbn):
    
    url = f'https://openapi.naver.com/v1/search/book.json?query={isbn}'
    headers = {
        "X-Naver-Client-Id": os.getenv('NAVER_CLIENT_ID'),
        "X-Naver-Client-Secret": os.getenv('NAVER_CLIENT_SECRET'),
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # isbn은 unique하므로, items의 첫번째 요소만 가져옴
        book_data = response.json().get('items')[0]
        return {
            'author': book_data.get('author'),
            'title': book_data.get('title'),
            'publisher': book_data.get('publisher'),
            'image': book_data.get('image'),
            'isbn': book_data.get('isbn'),
            'description': book_data.get('description'),
        }
    else:
        # Handle error or no data found
        return None

class BookRequestListView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_request.html'
    
    def get(self, request):
        book_requests = BookRequest.objects.all()
        book_list = []
        for book_request in book_requests:
            book_details = get_book_details_from_naver(book_request.request_isbn)
            if book_details:
                book_list.append({
                    'isbn': book_request.request_isbn,
                    'author': book_details['author'],
                    'title': book_details['title'],
                    'publisher': book_details['publisher'],
                    'request_count': book_request.request_count
                })

        book_list_sorted = sorted(book_list, key=lambda x: x['request_count'], reverse=True)
        context = {'book_list': book_list_sorted}
        return Response(context)


class BookRegisterView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_register.html'
    
    def get(self, request, book_isbn):
        book_details = get_book_details_from_naver(book_isbn)
        return Response(book_details)

    
class BookRegisterCompleteView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_register_complete.html'
    
    def post(self, request):
        # ISBN으로 이미 존재하는 책을 확인
        book_isbn = request.POST.get('book_isbn')
        # print(book_isbn, "book_isbn")
        try:
            existing_book = Book.objects.get(book_isbn=book_isbn)
            print("Book with this ISBN already exists.")
            # 책이 이미 존재하면 에러 메시지와 함께 종료
            return Response({
                'status': 'error',
                'message': 'Book with this ISBN already exists.'
            }, status=400)
        except Book.DoesNotExist:
            # 책이 존재하지 않으면 처리를 계속
            pass
        
        # 권한 확인
        if request.user.is_admin == False:
            print("You are not admin.")
            return Response({
                'status': 'error',
                'message': 'You are not admin.'
            }, status=403)
        
        # Naver API를 호출하여 책의 상세 정보를 가져옵니다.
        book_details = get_book_details_from_naver(book_isbn)
        if book_details is None:
            print("There is no book details.")
            return Response({
                'status': 'error',
                'message': 'Book details not found.'
            }, status=404)
            
        # Naver API로부터 받은 이미지 URL에서 이미지를 다운로드합니다.
        image_response = requests.get(book_details['image'])
        if image_response.status_code != 200:
            print(image_response.status_code)
            return Response({
                'status': 'error',
                'message': 'Failed to download book image.'
            }, status=400)
            
        content_file = request.FILES.get('book_content')
        if not content_file:
            print("No content file provided.")
            return Response({
                'status': 'error',
                'message': 'No content file provided.'
            }, status=400)


        # 가져온 상세 정보와 폼 데이터를 결합합니다.
        book_data = {
            'book_title': book_details['title'],
            'book_genre': request.POST.get('book_genre'), # 사용자 입력
            # 'book_image_path': ,
            'book_author': book_details['author'],
            'book_publisher': book_details['publisher'],
            'book_publication_date': datetime.date.today(),
            # 'book_content_path': ,
            'book_description': book_details['description'],
            'book_likes': 0,
            'book_isbn': book_isbn,
            'user': request.user.user_id,
        }

        # Serializer를 통해 데이터 검증 및 저장
        serializer = BookSerializer(data=book_data)
        if serializer.is_valid():
            book_instance = serializer.save()
            # 이미지와 텍스트 파일을 모델 인스턴스에 저장합니다.
            # 옵션 save=False 한 후 .save() 해서 한번에 저장
            book_instance.book_image_path.save(f"{book_isbn}_image.jpg", ContentFile(image_response.content), save=False)
            book_instance.book_content_path.save(content_file.name, content_file, save=False)
            book_instance.save()
            
        else:
            print(serializer.errors)
            return Response({
                'status': 'error',
                'message': 'Registration failed.',
                'errors': serializer.errors
            }, status=400)
        
        # BookRequest, UserRequest 삭제
        book_request = get_object_or_404(BookRequest, request_isbn=book_isbn)
        user_request_books = UserRequestBook.objects.filter(request=book_request)
        book_request.delete()
        user_request_books.delete()

        return Response({
            'status': 'success',
            'message': 'Book registered successfully.'
        }, status=200)
        
# 개인정보처리
def privacy_policy(request):
    return render(request, 'manager/privacy_policy.html')