from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    # 로그인/로그아웃
    path('', views.index, name='user_index'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('kakao', views.kakao_login, name='kakao_login'),
    path('kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('google', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('subscribe', views.SubscribeView.as_view(), name = 'subscribe'),

    # 계정관리

    # 도서 및 성우 내역

    # 문의내역
]
