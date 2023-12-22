from django.urls import path
from . import views

app_name = 'audiobook'  # audiobook:search

urlpatterns = [
    # 로그인
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),

    # 메인화면
    path('main/', views.MainView.as_view(), name='main'),
    path('genre/', views.genre, name='genre'),
    path('search/', views.search, name='search'),

    # 청취
    path('content/', views.content, name='content'),
    path('content/play/', views.content_play, name='content_play'),

    # 성우
    path('voice/custom/', views.voice_custom, name='voice_custom'),
    path('voice/celebrity/', views.voice_celebrity, name='voice_celebrity'),
    path('voice/custom/upload/', views.voice_custom_upload,
         name='vioce_custom_upload'),
    path('voice/custom/complete/', views.voice_custom_complete,
         name='vioce_custom_complete'),

]
