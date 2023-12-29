from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    # 로그인/로그아웃
    path('', views.index, name='user_index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('kakao/', views.kakao_login, name='kakao_login'),
    path('kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('google', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),

    # 계정관리
    path('profile/', views.UserSubscriptionView.as_view(), name='profile'),
    path('profile/information/', views.UserInformationView.as_view(),
         name='information'),


    # 도서 및 성우 내역
    path('profile/likebooks/', views.UserLikeBooksView.as_view(),
         name='like_books'),
    path('profile/likevoices/', views.UserLikeVoicesView.as_view(),
         name='like_voices'),
    path('profile/book_history/',
         views.UserBookHistoryView.as_view(), name='book_history'),

    # 문의내역
    path('profile/faq/', views.UserFAQView.as_view(), name='faq')
]
