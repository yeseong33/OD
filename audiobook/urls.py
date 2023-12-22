from django.urls import path
from . import views
from .views import helloAPI, voice_search

app_name = 'audiobook'  # audiobook:search


urlpatterns = [
    path('', views.index, name='index'),
    path('template', views.template, name='template'),
    path('main/', views.MainView.as_view(), name='main'),
    path('genre', views.genre, name='genre'),
    path('search', views.search, name='search'),
    path('content', views.content, name='content'),
    path('content/play', views.content_play, name='content_play'),
    path('voice/custom', views.voice_custom, name='voice_custom'),
    path('voice/celebrity', views.voice_celebrity, name='voice_celebrity'),
    path('voice/custom/upload', views.voice_custom_upload, name='vioce_custom_upload'),
    path('voice/custom/complete', views.voice_custom_complete, name='vioce_custom_complete'),
    path('login', views.login, name='login'),
    
]
