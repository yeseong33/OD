import json
import os
import requests
import datetime
import time
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import shutil

from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from community.models import BookRequest, UserRequestBook
from audiobook.models import Book
from user.models import Subscription
from .serializers import BookSerializer
from community.views import send_async_mail

load_dotenv()  # 환경 변수를 로드함


# 책 수요 변화

def book_view(request):
    return Response({'message': 'Good'})


def book_view_count(request):
    return Response({'message': 'Good'})


# 도서 신청 확인 페이지
def get_book_details_from_naver(isbn):

    # 캐시에서 데이터를 먼저 찾음
    cache_key = f'book_{isbn}'
    cached_data = cache.get(cache_key)
    print(cached_data)
    if cached_data:
        return json.loads(cached_data)

    # 캐시에 데이터가 없으면 API 호출
    url = f'https://openapi.naver.com/v1/search/book.json?query={isbn}'
    headers = {
        "X-Naver-Client-Id": os.getenv('NAVER_CLIENT_ID'),
        "X-Naver-Client-Secret": os.getenv('NAVER_CLIENT_SECRET'),
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # isbn은 unique하므로, items의 첫번째 요소만 가져옴
        book_data = response.json().get('items')[0]
        data = {
            'author': book_data.get('author'),
            'title': book_data.get('title'),
            'publisher': book_data.get('publisher'),
            'image': book_data.get('image'),
            'isbn': book_data.get('isbn'),
            'description': book_data.get('description'),
        }

        # 데이터를 캐시에 저장
        data = json.dumps(data)  # json 형태로 직렬화
        cache.set(cache_key, data, timeout=86400 * 7)  # 1주일 동안 캐시 유지
        return json.loads(data)  # 역직렬화하여 반환
    else:
        return None


class BookRequestListView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_request.html'

    def get(self, request):

        if not request.user.is_admin:
            return redirect('audiobook:main')

        book_requests = BookRequest.objects.all()
        book_list = []
        for book_request in book_requests:
            book_details = get_book_details_from_naver(
                book_request.request_isbn)
            if book_details:
                book_list.append({
                    'isbn': book_request.request_isbn,
                    'author': book_details['author'],
                    'title': book_details['title'],
                    'publisher': book_details['publisher'],
                    'request_count': book_request.request_count
                })

        book_list_sorted = sorted(
            book_list, key=lambda x: x['request_count'], reverse=True)

        # Paginator 설정
        paginator = Paginator(book_list_sorted, 10)
        page = request.GET.get('page')  # URL에서 페이지 번호 가져오기
        books = paginator.get_page(page)  # 해당 페이지의 책 가져오기
        context = {'book_list': books}

        return Response(context)


class BookRegisterView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_register.html'

    def get(self, request, book_isbn):
        if not request.user.is_admin:
            return redirect('audiobook:main')

        book_details = get_book_details_from_naver(book_isbn)
        if book_details:
            return Response(book_details)
        else:
            return Response({"error": "book_datail이 존재하지 않습니다"})


class BookRegisterCompleteView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_register_complete.html'

    def post(self, request):
        if not request.user.is_admin:
            return redirect('audiobook:main')

        print('request 디버깅')
        print(request.data)

        # ISBN으로 이미 존재하는 책을 확인
        book_isbn = request.POST.get('book_isbn')

        try:
            existing_book = Book.objects.get(book_isbn=book_isbn)
            print("이미 ISBN이 존재합니다.")
            # 책이 이미 존재하면 에러 메시지와 함께 종료
            return Response({
                'status': 'error',
                'message': '이미 ISBN이 존재합니다.'
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

        # Naver API를 호출하여 책의 상세 정보를 가져옴
        book_details = get_book_details_from_naver(book_isbn)
        print(book_details)
        if book_details is None:
            print("There is no book details.")
            return Response({
                'status': 'error',
                'message': 'Book details not found.'
            }, status=404)

        # 데이터 저장소에 파일을 저장
        # Naver API로부터 받은 이미지 URL에서 이미지를 다운로드
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

        # 가져온 상세 정보와 폼 데이터를 결합
        book_data = {
            'book_title': book_details['title'],
            'book_genre': request.POST.get('book_genre'),  # 사용자 입력
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
            # 이미지와 텍스트 파일을 모델 인스턴스에 저장
            # 옵션 save=False 한 후 .save() 해서 한번에 저장
            book_instance.book_image_path.save(
                f"{book_isbn}_image.jpg", ContentFile(image_response.content), save=False)
            book_instance.book_content_path.save(
                content_file.name, content_file, save=False)
            book_instance.save()

        else:
            print(serializer.errors)
            return Response({
                'status': 'error',
                'message': 'Registration failed.',
                'errors': serializer.errors
            }, status=400)

        # 이메일 보내기
        book_request = get_object_or_404(BookRequest, request_isbn=book_isbn)
        user_request_books = UserRequestBook.objects.filter(
            request=book_request)
        for user_request_book in user_request_books:
            user = user_request_book.user
            if user.email:
                try:
                    subject = '[오디 알림] 신청하신 책 등록 완료'
                    html_content = render_to_string(
                        'manager/email_template.html', {'nickname': user.nickname})
                    plain_message = strip_tags(html_content)
                    from_email = '오디 <wooyoung9654@gmail.com>'
                    send_async_mail(subject, plain_message,
                                    from_email, [user.email])
                    print('Email sent successfully')
                except Exception as e:
                    # 로그 기록, 오류 처리 등
                    print(f'Error sending email: {e}')

        # BookRequest, UserRequest 삭제
        book_request.delete()
        user_request_books.delete()

        return Response({
            'status': 'success',
            'message': 'Book registered successfully.'
        }, status=200)

# 개인정보처리


def privacy_policy(request):
    return render(request, 'manager/privacy_policy.html')


# 문의 답변

def inquiry(request):
    return Response({'message': 'Good'})


# 구독 및 수익 관리

def show_subscription(request):
    return render(request, 'manager/subscription.html')


class SubscriptionCountAPIView(APIView):
    def get(self, request, format=None):
        today = timezone.now().date()  # 'aware' 현재 날짜 객체
        dates = [today - relativedelta(months=n) for n in range(11, -1, -1)]

        data = {
            'dates': [],
            'counts': []
        }
        for date_point in dates:
            # 날짜를 'aware' datetime 객체로 변환
            aware_date_point = timezone.make_aware(
                datetime.combine(date_point, datetime.min.time()))

            count = Subscription.objects.filter(
                sub_start_date__lte=aware_date_point,
                sub_end_date__gte=aware_date_point
            ).count()
            data['dates'].append(aware_date_point.strftime('%Y-%m'))
            data['counts'].append(count)
        print(data)

        return Response(data)


# FAQ 관리


def faq(request):
    return Response({'message': 'Good'})

# 그래프, 책 표지 생성


@csrf_exempt
@require_http_methods(["POST", "GET"])
def cover_create(request):

    OPENAI_API_KEY = os.getenv('OPENAI_API')

    # 일단 바로 정의했는데, DB에 있는 데이터를 가져오도록 수정해야할듯.
    # book_title = '노인과 바다'
    # book_description = '주인공 산티아고 노인은 쿠바 섬 해변의 오두막집에서 혼자 사는 홀아비 어부이다. 고독한 처지이지만 고기잡이를 배우고자 그를 잘 따르는 마놀린이라는 소년이 이웃에 살고 있다. 소년은 노인에게 유일한 말동무이자 친구이자 생의 반려자가 되어 주고 가끔 음식도 갖다 준다.'

    MAX_RETRIES = 3  # 오류 뜰 경우 재시도 횟수

    if request.method == 'POST':
        data = json.loads(request.body)
        request_type = data.get('request_type')

        if request_type == 'create_graph':
            search_text = data.get('search_text')
            try:
                # 책 객체 조회
                book = Book.objects.get(book_title=search_text)
                # DB에서 책 제목과 설명 가져오기
                global book_title, book_description

                book_title = book.book_title
                book_description = book.book_description

                # 임시 수요 데이터 입력
                data = {
                    '1': 60,
                    '2': 60,
                    '3': 60,
                    '4': 60,
                    '5': 60,
                    '6': 10,
                    '7': 10,
                    '8': 10,
                    '9': 60,
                    '10': 10,
                    '11': 50,
                    '12': 10
                }
                json_data = json.dumps(data)
                book.book_view_count = json_data
                # 변경 사항 저장
                book.save()
            except Book.DoesNotExist:
                # 책이 존재하지 않는 경우 에러 처리
                return None

            # JSON 문자열을 파이썬 딕셔너리로 변환
            monthly_views = json.loads(book.book_view_count)
            months = list(range(1, 13))
            views = [monthly_views.get(str(month), 0) for month in months]

            # 그래프 생성
            plt.figure(figsize=(10, 6))
            plt.bar(months, views, color='skyblue')
            plt.xlabel('month')
            plt.ylabel('count')

            plt.title('book title of month count')
            plt.xticks(months)

            # 파일 경로 설정
            file_path = os.path.join('static', 'images', 'graph.png')

            # 그래프 파일로 저장
            plt.savefig(file_path)
            plt.close()  # 리소스 해제
            return JsonResponse({"message": "그래프가 성공적으로 생성되었습니다."}, status=200)
        elif request_type == 'create_cover':

            try:
                data = json.loads(request.body)
                selected_style = data.get('style', 'Disney style')
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON")

            def request_and_download_image(image_index, retry_count=0):
                api_url = 'https://api.openai.com/v1/images/generations'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                }
                data = {
                    "model": "dall-e-3",
                    "prompt": f"Book title: '{book_title}', Content: {book_description}. Please redraw the image in the style of {selected_style}.",
                    "n": 1,
                    "size": "1024x1024"
                }

                try:
                    response = requests.post(
                        api_url, headers=headers, data=json.dumps(data))
                    response.raise_for_status()

                    result = response.json()
                    image_url = result['data'][0]['url']

                    image_response = requests.get(image_url)
                    image_response.raise_for_status()

                    filename = os.path.join(
                        'static', 'images', f'Redraw_image_{image_index}.png')
                    with open(filename, 'wb') as file:
                        file.write(image_response.content)
                    print(f"Image {image_index} saved successfully.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                    if retry_count < MAX_RETRIES:
                        print(
                            f"Retrying... Attempt {retry_count + 1}/{MAX_RETRIES}")
                        time.sleep(1.5)
                        request_and_download_image(
                            image_index, retry_count + 1)
                    else:
                        print(
                            f"Maximum retry attempts for image {image_index} reached. Aborting.")

            def make_parallel_requests():
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(
                        request_and_download_image, i) for i in range(3)]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()

            make_parallel_requests()
            return JsonResponse({"message": "표지가 성공적으로 생성되었습니다."}, status=200)

        elif request_type == 'update_cover':
            data = json.loads(request.body)
            image_number = data.get('image_number')

            # 이미지 번호를 기반으로 새 이미지 경로 설정
            new_image_path = os.path.join(
                'static', 'images', f'Redraw_image_{image_number}.png')

            # 기존 이미지 경로 설정
            existing_image_path = os.path.join(
                'static', 'images', 'origin_image.png')

            # 기존 이미지를 새 이미지로 교체
            if os.path.exists(new_image_path):
                shutil.copy(new_image_path, existing_image_path)
                return JsonResponse({'status': 'success', 'message': 'Cover image updated successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'New image not found.'})

    elif request.method == 'GET':
        return render(request, 'manager/book_cover.html')
    return HttpResponse("적절한 응답 메시지")


def cover_complete(request):
    return render(request, 'manager/book_complete.html')
