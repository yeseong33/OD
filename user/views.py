# 표준 라이브러리
import os
from datetime import datetime, timedelta

# 제3자 라이브러리
import bcrypt
import requests
from dotenv import load_dotenv
from jose import jwt

# Django 관련 임포트
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

# Django REST framework 관련 임포트
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer

# 로컬 애플리케이션/모델 관련 임포트
from .models import *  # 이 부분은 구체적인 모델 이름을 명시하는 것이 좋습니다.
from audiobook.models import *  # 이 부분도 마찬가지입니다.
from community.models import Inquiry
from audiobook.serializers import VoiceSerializer
from community.serializers import BookSerializer, InquirySerializer
from user.serializers import UserSerializer, SubscriptionSerializer
from config.settings import AWS_S3_CUSTOM_DOMAIN, MEDIA_URL, FILE_SAVE_POINT, MEDIA_ROOT
from django.conf import settings

load_dotenv()


def index(request):
    return render(request, 'user/index.html')


def login(request):
    return render(request, 'user/login.html')


def logout(request):
    response = redirect('audiobook:index')  # 첫 화면으로 리다이렉트
    response.delete_cookie('jwt')
    return response


def sign_in(user_data):
    user_serializer = UserSerializer(data=user_data)

    if user_serializer.is_valid():
        user = user_serializer.save()
        sub_serializer = SubscriptionSerializer(
            data={'user': user.user_id, 'is_subscribed': False})
        if sub_serializer.is_valid():
            sub_serializer.save()
        return user


def kakao_login(request):
    print("kakao Login 클릭")
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI_PRODUCTION')
        print('in production')

    return redirect(f"https://kauth.kakao.com/oauth/authorize?client_id={os.getenv('KAKAO_CLIENT_ID')}&redirect_uri={redirect_uri}&response_type=code")


def kakao_callback(request):
    # 환경에 따른 redirect_uri 설정
    print("kakao_callback 호출")
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('KAKAO_REDIRECT_URI_PRODUCTION')
        print('in production')

    # access_token 발급
    code = request.GET.get('code')
    url = "https://kauth.kakao.com/oauth/token"
    headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv('KAKAO_CLIENT_ID'),
        "redirect_uri":  redirect_uri,
        "code": request.GET.get('code')
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = response.json().get('access_token')

    # access_token으로 유저 개인 정보 발급 받기
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}",
               "Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
    response = requests.post(url, headers=headers)
    user_inform = response.json().get('kakao_account')

    try:  # email DB 여부 조회.
        user = User.objects.get(email=user_inform['email'])
    except User.DoesNotExist:
        email = user_inform['email']
        user_data = {
            'nickname': user_inform['profile']['nickname'],
            'email': email,
            'password': os.getenv('USER_PASSWORD'),
            'oauth_provider': 'Kakao',
            'username': email,
        }

        thumbnail_image_url = response.json().get('properties')[
            'thumbnail_image']
        thumbnail_image_response = requests.get(thumbnail_image_url)
        file_name = email.replace('@', '_at_')  # file 시스템에서 @를 쓰지못하게해서 변경.
        user_data['user_profile_path'] = ContentFile(
            thumbnail_image_response.content, name=f"{file_name}_profile.jpg")
        user = sign_in(user_data)

    token = get_jwt_token(user)
    response = redirect("audiobook:main")
    response.set_cookie("jwt", token)
    return response


def google_login(request):
    print("google Login 클릭")
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        print('in local')
    else:
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI_PRODUCTION')
        print('in production')

    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={redirect_uri}&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email")


def google_callback(request):
    # 환경에 따른 redirect_uri 설정
    if settings.SETTINGS_MODULE == 'config.settings_local':
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    else:
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI_PRODUCTION')

    # access_token 발급 받기
    url = "https://oauth2.googleapis.com/token"
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret":  os.getenv('GOOGLE_SECRET_KEY'),
        "code": request.GET.get('code'),
        "redirect_uri": redirect_uri,
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = response.json().get('access_token')

    # user_inform 받기
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url=url, headers=headers)

    try:  # email DB 여부 조회.
        user = User.objects.get(email=response.json()['email'])
    except User.DoesNotExist:
        email = response.json()['email']
        user_data = {
            'nickname': response.json()['name'],
            'email': email,
            # Assuming you have a predefined password in your .env file
            'password': os.getenv('USER_PASSWORD'),
            'oauth_provider': 'Google',
            'username': email,
        }
        thumbnail_image_url = response.json()['picture']
        thumbnail_image_response = requests.get(thumbnail_image_url)

        # 이미지를 ContentFile로 변환하여 저장
        thumbnail_image_url = response.json()['picture']
        thumbnail_image_response = requests.get(thumbnail_image_url)
        file_name = email.replace('@', '_at_')  # file 시스템에서 @를 쓰지못하게해서 변경.
        user_data['user_profile_path'] = ContentFile(
            thumbnail_image_response.content, name=f"{file_name}_profile.jpg")
        user = sign_in(user_data)

    token = get_jwt_token(user)
    response = redirect("audiobook:main")
    response.set_cookie("jwt", token)
    return response


# 사용자 정보를 바탕으로 JWT 토큰 발급
def get_jwt_token(user):
    print(f"create jwt 메소드 진입.")
    payload = {"user_id": user.user_id, "user_email": user.email,
               "exp": datetime.utcnow() + timedelta(hours=24)}
    secret_key = os.getenv("JWT_SECRET_KEY")
    token = jwt.encode(payload, secret_key,
                       algorithm=os.getenv("JWT_ALGORITHM"))

    print(f"JWT token 생성 완료 : {token}")
    decode_jwt(token)
    return token

# JWT 복호화


def decode_jwt(token):
    user_inform = jwt.decode(token, key=os.getenv(
        "JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")])
    return user_inform

# 결제
# def payments(request):
#     user = request.user  # Django의 인증 시스템을 통해 현재 로그인한 사용자를 가져옵니다.
    
#     if not user.is_authenticated:
#         return redirect('user:login')  # 로그인하지 않은 사용자는 로그인 페이지로 리다이렉션합니다.

#     if request.method == "POST":
#         # 주문번호 생성 로직
#         date_str = datetime.now().strftime("%Y%m%d")  # 현재 날짜를 YYYYMMDD 형식으로 가져옵니다.
#         last_order = Subscription.objects.filter(sub_payment_status='pending').last()
        
#         if last_order:
#             last_order_id = last_order.partner_order_id
#             order_num = int(last_order_id.split(date_str)[-1]) + 1  # 마지막 주문번호에서 숫자 부분을 추출하여 1을 더합니다.
#         else:
#             order_num = 1  # 주문이 없는 경우 1부터 시작합니다.

#         partner_order_id = f"{date_str}{order_num:04d}"  # 새로운 주문번호를 생성합니다.
#         request.session['partner_order_id'] = partner_order_id

#         # 결제 API 요청을 위한 URL 및 헤더
#         URL = 'https://kapi.kakao.com/v1/payment/ready'
#         headers = {
#             "Authorization": "KakaoAK " + os.environ.get('KAKAO_API_KEY'),  # 환경 변수에서 API 키를 가져옵니다.
#             "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
#         }

#         # 결제 요청 파라미터
#         params = {
#             "cid": "TC0ONETIME",  # 테스트용 코드
#             "partner_order_id": partner_order_id,  # 생성한 주문번호
#             "partner_user_id": user.user_id,  # 로그인한 사용자의 user_id
#             "item_name": "1개월 구독",  # 구매 물품 이름
#             "quantity": "1",  # 구매 물품 수량
#             "total_amount": "1",  # 구매 물품 가격
#             "tax_free_amount": "0",  # 구매 물품 비과세
#             "approval_url": request.build_absolute_uri(reverse('user:approval')),  # 결제 성공 시 이동할 URL
#             "cancel_url": request.build_absolute_uri(request.get_full_path()),  # 결제 취소 시 이동할 URL
#             "fail_url": request.build_absolute_uri(request.get_full_path()),  # 결제 실패 시 이동할 URL
#         }

#         # 결제 요청을 보냅니다.
#         res = requests.post(URL, headers=headers, params=params)
#         if res.status_code != 200:
#             # 요청에 실패한 경우, 오류 메시지를 표시할 수 있습니다.
#             return HttpResponse('결제 준비 요청에 실패하였습니다.', status=500)

#         # 결제 승인시 사용할 tid를 세션에 저장하고, 결제 페이지로 넘어갈 URL을 저장합니다.
#         request.session['tid'] = res.json()['tid']  
#         next_url = res.json()['next_redirect_pc_url']  
#         return redirect(next_url)
    
#     # POST 요청이 아닌 경우 결제 페이지를 렌더링합니다.
#     return render(request, 'payments/payments.html')
    
# def approval(request):
#     partner_order_id = request.session.get('partner_order_id')
#     user = request.user
#     tid = request.session.get('tid')
#     pg_token = request.GET.get("pg_token")

#     if not partner_order_id or not tid or not pg_token:
#         # 필요한 세션 데이터 또는 pg_token이 없을 경우 오류 처리
#         return HttpResponse('필요한 결제 정보가 없습니다.', status=400)

#     URL = 'https://kapi.kakao.com/v1/payment/approve'
#     headers = {
#         "Authorization": "KakaoAK " + os.environ.get('KAKAO_API_KEY'),
#         "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
#     }
#     params = {
#         "cid": "TC0ONETIME",
#         "tid": tid,
#         "partner_order_id": partner_order_id,
#         "partner_user_id": user.id,  # user_id 대신 id를 사용
#         "pg_token": pg_token,
#     }

#     res = requests.post(URL, headers=headers, params=params)

#     if res.status_code != 200:
#         # 결제 승인 요청에 실패한 경우 오류 처리
#         return HttpResponse('결제 승인 요청에 실패하였습니다.', status=500)

#     res_json = res.json()
#     amount = res_json['amount']['total']
#     context = {
#         'amount': amount,
#         'res': res_json
#     }

#     return render(request, 'payments/approval.html', context)


class SubscribeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        if not request.user.is_authenticated:  # User가 로그인 안 했을 시
            print("user가 로그인하지 않고 Subscribe 페이지 접속.")
            return redirect('user:login')
        
        user = request.user
        subscription, created = Subscription.objects.get_or_create(user=user)

        left_days = (subscription.sub_end_date - timezone.now()).days if subscription.sub_end_date else 0

        if subscription.is_subscribed:
            # 구독중인 경우
            template_name = 'user/pay_inform.html'
        else:
            # 구독중이지 않은 경우
            template_name = "user/non_pay_inform.html"

        context = {
            'user': user,
            'left_days': left_days,
            'active_tab': 'user_subscription'
        }

        return Response(context, template_name=template_name)
        
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
        
        user = request.user
        subscription, created = Subscription.objects.get_or_create(user=user)
        
        # 구독이 새롭게 생성되었거나 아직 구독되지 않았다면,
        if created or not subscription.is_subscribed:
            # 최초 구독인 경우, 구독 시작일을 현재로 설정
            if created or subscription.sub_start_date is None:
                subscription.sub_start_date = timezone.now()
            
            # 구독을 활성화하고 상태를 'success'로 변경
            subscription.is_subscribed = True
            subscription.sub_payment_status = 'success'
            
            # 구독 종료일이 이미 설정되어 있지 않거나 과거일 경우, 현재부터 한달 후로 갱신
            if not subscription.sub_end_date or subscription.sub_end_date < timezone.now():
                subscription.sub_end_date = timezone.now() + timedelta(days=30)
            
            subscription.save()  # 변경사항을 저장
            
            return redirect('user:pay_inform')
        else:
            # 이미 구독 중인 경우, 구독 종료일만 갱신
            if subscription.sub_end_date and subscription.sub_end_date > timezone.now():
                # 기존 구독의 종료일이 현재보다 미래인 경우에만 갱신
                subscription.sub_end_date += timedelta(days=30)
                subscription.save()

            return redirect('user:pay_inform')
def cancel_subscription(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    user = request.user
    try:
        subscription = Subscription.objects.get(user=user, is_subscribed=True)
        subscription.is_subscribed = False
        subscription.sub_payment_status = 'pending'  # 결제 상태를 'cancelled'로 변경
        subscription.save()
        return JsonResponse({'success': '구독이 취소되었습니다.'})
    except Subscription.DoesNotExist:
        return JsonResponse({'error': '구독 정보가 없습니다.'}, status=404)
    
def pay_inform_view(request):
    if not request.user.is_authenticated:
        return redirect('user:login')

    try:
        subscription = Subscription.objects.get(user=request.user)
        
        # 구독 시작일로부터 현재까지의 개월 수 계산
        if subscription.sub_start_date:
            months_subscribed = (timezone.now().date() - subscription.sub_start_date.date()).days // 30
            # 다음 자동 결제일 계산
            next_payment_date = subscription.sub_start_date.date() + timedelta(days=(months_subscribed + 1) * 30)
        else:
            months_subscribed = 0
            next_payment_date = None

        # 잔여일수 계산
        left_days = (subscription.sub_end_date - timezone.now()).days if subscription.sub_end_date else 0

        context = {
            'user': request.user,
            'sub_start_date': subscription.sub_start_date,
            'months_subscribed': months_subscribed,
            'next_payment_date': next_payment_date,
            'left_days': left_days,
        }
    except Subscription.DoesNotExist:
        context = {
            'user': request.user,
            'sub_start_date': None,
            'months_subscribed': 0,
            'next_payment_date': None,
            'left_days': 0,
        }

    return render(request, 'user/pay_inform.html', context)

class UserInformView(APIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        template_name = 'user/user_inform.html'
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        serializer = UserSerializer(user)

        context = {
            'user': serializer.data,
            'active_tab': 'user_information',
        }

        return Response(context, template_name=template_name)

    def post(self, request):
        file_path = get_file_path(self)
        # cookie에 저장된 jwt 정보를 이용해 유저 받아오기
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])

        user_image = request.FILES.get('file')
        nickname = request.POST.get('nickname')

        # 사진 저장 로직 구현 필요. 보류 아마존 s3 버킷에 이미지를 저장.
        if user_image or nickname:
            if user_image:
                temp_file_name = user.email.replace('@', '_at_')
                file_name = f"user_images/{temp_file_name}_profile.jpg"
                file_path += file_name
                if FILE_SAVE_POINT == 'local':
                    # 기존에 유저 이미지 파일 삭제.
                    os.remove(os.path.join(
                        MEDIA_ROOT, str(user.user_profile_path)))

                    local_file_path = os.path.join(MEDIA_ROOT, file_name)
                    with open(local_file_path, 'wb') as local_file:
                        for chunk in user_image.chunks():
                            local_file.write(chunk)
            if nickname:  # body에 들어있다면 nickname이 들어있다면 변경
                user.nickname = nickname
            user.save()

        messages.success(request, '정보가 성공적으로 변경되었습니다.')
        return redirect('user:inform')


class UserLikeBooksView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/like_books.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        book_id_list = user.user_favorite_books

        if book_id_list is None:  # 유저가 좋아요한 목록이 없을 경우.
            context = {
                'books': None,
                'active_tab': 'user_like'
            }
        else:
            # 정렬 방식을 라디오 버튼 값으로 받아오기
            order_by = request.GET.get('orderBy', 'latest')
            books = Book.objects.filter(pk__in=book_id_list)
            if order_by == 'title':
                books = books.order_by('book_title')
            else:
                books = books.order_by('book_id')
            serializer = BookSerializer(books, many=True)
            context = {
                'books': serializer.data,
                'active_tab': 'user_like'

            }

        # 만약 요청이 Ajax라면 JSON 형식으로 응답
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)

        # 일반적인 GET 요청이라면 HTML 렌더링
        return render(request, self.template_name, context)


class UserLikeVoicesView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/like_voices.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        voice_id_list = user.user_favorite_voices  # 유저가 좋아요한 책 Pk를 조회

        if voice_id_list == None:
            context = {'voices': None,
                       'active_tab': 'user_like'}
        else:
            order_by = request.GET.get('orderBy', 'latest')
            voice_list = Voice.objects.filter(pk__in=voice_id_list)

            if order_by == 'name':
                voice_list = voice_list.order_by('-voice_name')
            else:
                voice_list = voice_list.order_by('voice_id')

            serializer = VoiceSerializer(voice_list, many=True)
            context = {'voices': serializer.data,
                       'active_tab': 'user_like'}

        # Ajax 요청일경우.
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)

        # Ajax 요청이 아닐경우.
        return render(request, self.template_name, context)


class BookHistoryView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/book_history.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        user = User.objects.get(user_id=user_inform['user_id'])
        book_id_list = user.user_book_history  # 유저 독서이력을 조회.

        if book_id_list == None:  # 유저가 좋아요한 목록이 없을 경우.
            context = {
                'books': None,
                'active_tab': 'user_book_history',
            }
        else:
            # 정렬 방식을 라디오 버튼 값으로 받아오기
            order_by = request.GET.get('orderBy', 'latest')
            books = Book.objects.filter(pk__in=book_id_list)
            if order_by == 'title':
                books = books.order_by('book_title')
            else:
                books = books.order_by('book_id')

            serializer = BookSerializer(books, many=True)

            context = {
                'books': serializer.data,
                'active_tab': 'user_book_history'
            }
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(context)

        return render(request, self.template_name, context)


class InquiryListView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/inquiry_list.html'

    def get(self, request):
        user_inform = decode_jwt(request.COOKIES.get("jwt"))
        inquiry_list = Inquiry.objects.filter(
            user_id__in=[user_inform['user_id']])
        if not inquiry_list:
            context = {
                'inquiries': None,
                'active_tab': 'user_faq'
            }
        else:
            serializer = InquirySerializer(inquiry_list, many=True)
            context = {'inquiries': serializer.data,
                       'active_tab': 'user_faq'}

        return render(request, self.template_name, context)


class InquiryDetailView(APIView):  # 세부 1:1 문의 내역 보는 view
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'user/inquiry_detail.html'

    def get(self, request, inquiry_id):
        inquiry = Inquiry.objects.get(inquiry_id=inquiry_id)
        serializer = InquirySerializer(inquiry)
        context = {'inquiry': serializer.data,
                   'active_tab': 'user_faq'}
        return render(request, self.template_name, context)


class UserDeleteView(APIView):  # 회원탈퇴 함수.
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/index.html'  # 탈퇴하면 index.html로 이동.

    def get(self, request, user_id):

        user = User.objects.get(user_id=user_id)
        # 유저 이미지 삭제.
        os.remove(os.path.join(MEDIA_ROOT, str(user.user_profile_path)))
        user.delete()  # 유저 테이블 삭제.
        response = redirect('audiobook:index')
        response.delete_cookie('jwt')  # 유저 쿠키 삭제.
        messages.success(request, '계정이 삭제되었습니다.')
        return (response)


def get_file_path(self):
    if FILE_SAVE_POINT == 'local':
        return MEDIA_URL
    else:
        return AWS_S3_CUSTOM_DOMAIN
