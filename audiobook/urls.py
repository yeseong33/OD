from django.urls import path
from . import views
from .views import helloAPI, voice_search

app_name = 'audiobook'  # audiobook:search


urlpatterns = [
    # 첫 화면
    path('', views.index, name='index'),

    # 메인화면
    path('main/', views.MainView.as_view(), name='main'),
    path('main/search/', views.main_search, name='main_search'),
    path('api/book/list/', views.BookListAPI.as_view(), name='api_book_list'),
    path('main/genre/', views.MainGenreView.as_view(), name='main_genre'),

    # 청취
    path('content/<int:book_id>', views.ContentHTML.as_view(), name='content'),
    path('content/play/<int:book_id>',
         views.ContentPlayHTML.as_view(), name='content_play'),

    # 성우
    path('voice/custom/<int:book_id>', views.VoiceCustomHTML.as_view(), name='voice_custom'),
    path('voice/celebrity/<int:book_id>', views.VoiceCelebrityHTML.as_view(),
         name='voice_celebrity'),
    path('voice/custom/upload/<int:book_id>', views.voice_custom_upload.as_view(),
         name='voice_custom_upload'),
    path('voice/custom/complete/<int:book_id>', views.voice_custom_complete.as_view(),
         name='voice_custom_complete'),
    path('voice/custom/complete/upload', views.voice_custom_upload_post,
         name='voice_custom_upload_post'),
    path('voice/custom/search/', views.Voice_Custom_Search.as_view(),
         name='voice_custom_search')
]
