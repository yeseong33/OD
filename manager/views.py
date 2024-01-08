from django.core.files import File
from config.context_processors import get_file_path
from config.settings import FILE_SAVE_POINT
from botocore.exceptions import NoCredentialsError
import boto3
import matplotlib.font_manager as fm
from django.contrib import messages
import json
import os
from django.urls import reverse
import requests
import datetime
import time
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import shutil
# 표준 라이브러리
from manager.forms import InquiryResponseForm
from community.views import send_async_mail
from manager.serializers import InquirySerializer
from user.models import Subscription
from audiobook.models import Book
from community.models import BookRequest, UserRequestBook, Inquiry
from rest_framework import status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.template.loader import render_to_string
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.core.cache import cache
from dotenv import load_dotenv
import concurrent.futures
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import json
import os
import shutil
import time
import datetime
from datetime import datetime as dt
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from community.serializers import BookSerializer
from .models import FAQ
from .serializers import FAQSerializer

# 외부 라이브러리
import numpy as np
import requests
import matplotlib
matplotlib.use('Agg')
matplotlib.use('Agg')


load_dotenv()  # 환경 변수를 로드함


# 데코레이터 설정
def is_specific_user_condition(user):
    # 여기에 특정 사용자 속성을 만족시키는 조건을 작성
    return user.is_authenticated and user.is_admin == True


specific_user_required = user_passes_test(
    is_specific_user_condition, login_url='manager:access_deny')


# 책 수요 변화

def book_view_count(request):
    return Response({'message': 'Good'})


@csrf_exempt
@specific_user_required
@require_http_methods(["POST", "GET"])
def book_view(request):

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    MAX_RETRIES = 3  # 오류 뜰 경우 재시도 횟수

    if request.method == 'POST':
        data = json.loads(request.body)
        request_type = data.get('request_type')

        if request_type == 'create_graph':
            search_text = data.get('search_text')
            try:

                global book_title, book_description, book_id, book_image_path, book
                # 책 객체 조회
                book = Book.objects.get(book_title=search_text)
                # DB에서 책 제목과 설명 가져오기
                book_title = book.book_title
                book_description = book.book_description
                book_id = book.book_isbn
                book_image_path = book.book_image_path

                # book_view_count 데이터 확인
                if book.book_view_count:
                    # JSON 문자열을 파이썬 딕셔너리로 변환
                    monthly_views = json.loads(book.book_view_count)
                else:
                    # 임시 수요 데이터 입력
                    monthly_views = {
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
                    book.book_view_count = json.dumps(monthly_views)
                    book.save()

            except Book.DoesNotExist:
                # 책이 존재하지 않는 경우 에러 처리
                return None

            # 데이터 설정
            months = list(range(1, 13))
            views = [monthly_views.get(str(month), 0) for month in months]

            # 폰트 파일 경로 설정
            font_path = os.path.join('static', 'fonts', 'NotoSansKR-Light.ttf')

            # Matplotlib 폰트 설정
            font_prop = fm.FontProperties(fname=font_path, size=12)

            # 그래프 생성
            plt.figure(figsize=(10, 6))
            plt.bar(months, views, color='skyblue')
            plt.xlabel('월별', fontproperties=font_prop)
            plt.ylabel('사용량', fontproperties=font_prop)

            plt.title(f'<{book_title}> 월별 사용자 추이', fontproperties=font_prop)
            plt.xticks(months)

            # 축 레이블에 폰트 적용
            for label in (plt.gca().get_xticklabels() + plt.gca().get_yticklabels()):
                label.set_fontproperties(font_prop)

            # 파일 경로 설정 및 그래프 저장
            file_path = os.path.join('static', 'images', 'graph.png')
            plt.savefig(file_path)
            plt.close()
            return JsonResponse({"message": "그래프가 성공적으로 생성되었습니다."}, status=200)

        elif request_type == 'search':
            data = json.loads(request.body)
            search_query = data.get('search_query', '').strip()

            if search_query:
                # 책 제목이 검색 쿼리를 포함하는 모든 책을 검색
                books = Book.objects.filter(book_title__icontains=search_query)
                results = [{'title': book.book_title} for book in books]
                # print(results)
                return JsonResponse({'books': results}, safe=False)

            return JsonResponse({'books': []})

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
            # 새 이미지 파일 경로
            new_image_path = f'static/images/Redraw_image_{image_number}.png'

            if FILE_SAVE_POINT == 'local':
                try:
                    # 새 이미지 파일을 Django의 File 객체로 열기
                    with open(new_image_path, 'rb') as new_image_file:
                        django_file = File(new_image_file)
                        # 모델의 이미지 필드에 File 객체를 할당
                        current_filename = os.path.basename(
                            book_image_path.name)
                        book_image_path.save(
                            current_filename, django_file, save=True)

                    return JsonResponse({'status': 'success', 'message': '커버 이미지가 성공적으로 업데이트되었습니다.'})

                except Book.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': '해당 책이 존재하지 않습니다.'})
                except IOError:
                    return JsonResponse({'status': 'error', 'message': '이미지 파일을 열 수 없습니다.'})

            else:

                # S3 클라이언트 생성
                s3 = boto3.client('s3')
                s3_bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
                bucket_name = s3_bucket_name  # S3 버킷 이름

                # S3 버킷 내 기존 이미지 파일 경로
                existing_image_path = str(book_image_path)
                try:
                    # 새 이미지 파일을 S3 버킷으로 업로드
                    s3.upload_file(new_image_path, bucket_name,
                                   existing_image_path)
                    return JsonResponse({'status': 'success', 'message': 'Cover image updated successfully.'})
                except FileNotFoundError:
                    return JsonResponse({'status': 'error', 'message': 'New image not found.'})
                except NoCredentialsError:
                    return JsonResponse({'status': 'error', 'message': 'Credentials not available.'})

    elif request.method == 'GET':
        return render(request, 'manager/book_cover.html')
    return HttpResponse("적절한 응답 메시지")


@specific_user_required
def cover_complete(request):
    return render(request, 'manager/book_complete.html')


# 도서 신청 확인

def get_book_details_from_naver(isbn):

    # 캐시에서 데이터를 먼저 찾음(redis)
    cache_key = f'book_{isbn}'
    cached_data = cache.get(cache_key)
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


@method_decorator(specific_user_required, name='dispatch')
class BookRequestListView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/book_request.html'

    def get(self, request):
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


@method_decorator(specific_user_required, name='dispatch')
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


@method_decorator(specific_user_required, name='dispatch')
class BookRegisterAPIView(APIView):
    def post(self, request):
        book_isbn = request.POST.get('book_isbn')

        # Naver API를 호출하여 책의 상세 정보를 가져옴
        book_details = get_book_details_from_naver(book_isbn)
        # print(book_details)
        if book_details is None:
            print("There is no book details.")
            return Response({
                'status': 'error',
                'message': 'Book details not found.'
            }, status=404)

        
        # 새로운 Book 인스턴스 생성
        
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
            # 책 저장하기
            # 이미지와 텍스트 파일을 모델 인스턴스에 저장
            # 옵션 save=False 한 후 .save() 해서 한번에 저장
            book_instance.book_image_path.save(
                f"{book_isbn}_image.jpg", ContentFile(image_response.content), save=False)
            book_instance.book_content_path.save(
                content_file.name, content_file, save=False)
            book_instance.save()

            # 이메일 보내기
            book_request = get_object_or_404(
                BookRequest, request_isbn=book_isbn)
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
                        # print('Email sent successfully')
                    except Exception as e:
                        # 로그 기록, 오류 처리 등
                        print(f'Error sending email: {e}')

            # BookRequest, UserRequest 삭제
            book_request.delete()
            user_request_books.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Book registered successfully.'
            })

        else:
            print(serializer.errors)
            return Response({
                'status': 'error',
                'message': 'Registration failed.',
                'errors': serializer.errors
            }, status=400)


# 문의 답변


@specific_user_required
def inquiry_list(request):  # 문의글 목록 페이지
    return render(request, 'manager/inquiry_list.html')


@specific_user_required
def inquiry_detail(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, pk=inquiry_id)

    if request.method == 'POST':
        form = InquiryResponseForm(request.POST)
        if form.is_valid():
            inquiry.inquiry_response = form.cleaned_data['response']
            inquiry.inquiry_is_answered = True
            inquiry.inquiry_answered_date = timezone.now()
            inquiry.save()

            serializer = InquirySerializer(inquiry)
            return JsonResponse(serializer.data, safe=False)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    else:
        form = InquiryResponseForm()

    return render(request, 'manager/inquiry_detail.html', {'inquiry': inquiry, 'form': form})


@method_decorator(specific_user_required, name='dispatch')
class InquiryListAPI(APIView):
    def get(self, request, *args, **kwargs):
        show_answered = request.query_params.get('show_answered', 'all')
        if show_answered == 'answered':
            inquiries = Inquiry.objects.filter(inquiry_is_answered=True)
        elif show_answered == 'not_answered':
            inquiries = Inquiry.objects.filter(inquiry_is_answered=False)
        else:
            inquiries = Inquiry.objects.all()

        # 여러 인스턴스 직렬화
        serializer = InquirySerializer(inquiries, many=True)
        return Response(serializer.data)


@method_decorator(specific_user_required, name='dispatch')
class InquiryDetailAPI(APIView):
    def get(self, request, inquiry_id, format=None):
        inquiry = get_object_or_404(Inquiry, pk=inquiry_id)
        serializer = InquirySerializer(inquiry)
        return Response(serializer.data)


# 구독 및 수익 관리
@specific_user_required
def show_subscription(request):
    return render(request, 'manager/subscription.html')


@method_decorator(specific_user_required, name='dispatch')
class SubscriptionCountAPI(APIView):
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
                dt.combine(date_point, dt.min.time()))

            count = Subscription.objects.filter(
                sub_start_date__lte=aware_date_point,
                sub_end_date__gte=aware_date_point
            ).count()
            data['dates'].append(aware_date_point.strftime('%Y-%m'))
            data['counts'].append(count)
        # print(data)

        return Response(data)


# FAQ 관리
@method_decorator(specific_user_required, name='dispatch')
class ManagerFAQHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/faq.html'

    def get(self, request):
        faqs = FAQ.objects.all()
        serializers = FAQSerializer(faqs, many=True)
        context = {
            'active_tab': 'book_faq',
            'faqs': serializers.data,
        }
        return Response(context, template_name=self.template_name)


@method_decorator(specific_user_required, name='dispatch')
class ManagerFAQPostHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/faq_post.html'

    def get(self, request):
        faqs = FAQ.objects.all()
        serializers = FAQSerializer(faqs, many=True)
        context = {
            'active_tab': 'book_faq',
            'faqs': serializers.data,
        }
        return Response(context, template_name=self.template_name)


# 접근 제한

class AccessDenyHtml(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manager/access_deny.html'

    def get(self, request):
        return Response(template_name=self.template_name)

# 삭제 버튼


@require_http_methods(["POST"])
def book_delete(request):
    # POST 요청에서 ISBN을 가져옴
    book_isbn = request.POST.get('book_isbn')
    book_request = get_object_or_404(BookRequest, request_isbn=book_isbn)
    user_request_books = UserRequestBook.objects.filter(request=book_request)
    book_request.delete()
    user_request_books.delete()
    try:
        # 해당 ISBN을 가진 도서를 찾아 삭제
        book = Book.objects.get(book_isbn=book_isbn)
        book.delete()
        messages.success(request, '도서가 성공적으로 삭제되었습니다.')
    except Book.DoesNotExist:
        # 도서가 존재하지 않는 경우 에러 메시지를 추가
        messages.error(request, '해당 도서를 찾을 수 없습니다.')

    # 삭제 후 관리자 페이지로 응답
    return JsonResponse({'redirect_url': reverse('manager:book_request')})
