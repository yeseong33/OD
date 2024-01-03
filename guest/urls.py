from django.urls import path, include
from . import views

app_name = 'guest'

urlpatterns = [
    # 첫 화면
    path('', views.IndexHTML.as_view(), name='main'),

    # path('test/', views.test, name='test'),

    # # 메인화면
    # path('main/', views.MainView.as_view(), name='main'),
    # path('main/search/', views.MainSearchView.as_view(), name='main_search'),
    # path('main/genre/', views.MainGenreView.as_view(), name='main_genre'),

    # # 청취
    # path('content/<int:book_id>', views.ContentHTML.as_view(), name='content'),
    # path('content/play/<int:book_id>',
    #      views.ContentPlayHTML.as_view(), name='content_play'),

    # # 성우
    # path('voice/custom/', views.voice_custom, name='voice_custom'),
    # path('voice/celebrity/', views.voice_celebrity, name='voice_celebrity'),
    # path('voice/custom/upload/', views.voice_custom_upload,
    #      name='voice_custom_upload'),
    # path('voice/custom/complete/', views.voice_custom_complete,
    #      name='voice_custom_complete'),
    # path('voice/custom/complete/upload', views.voice_custom_upload_post,
    #      name='voice_custom_upload_post'),

    # # 개인정보처리
    # path('privacy_policy/', views.privacy_policy, name='privacy_policy'),

    # # rvc train
    # path('rvc_train/', views.Rvc_Train.as_view(), name='rvc_train'),
    # path('rvc_save/', views.Rvc_Save, name='rvc_save'),
    # path('rvc_cancel/', views.Rvc_Cancel, name='rvc_cancel'),
    # path('tts/', views.TTS, name="TTS")

    # html render
    # 토론
    # path('books/share/', views.BookShareHtml.as_view(), name='book_share'),
    # path('books/share/content/<int:pk>', views.BookShareContentHtml.as_view(), name='book_share_content'),
    # path('books/share/content/post/', views.BookShareContentPostHtml.as_view(), name='book_share_content_post'),
    # path('books/share/content/post/detail/<int:pk>', views.BookShareContentPostDetailHtml.as_view(), name='book_share_content_post_detail'),
    

    # # 신규 도서 신청
    # # http://127.0.0.1:8000/community/books/search
    # path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    # path('books/search/<int:isbn>/', views.BookCompleteView.as_view(), name='book_complete'),

    # # 1:1 문의
    # path('books/inquiry/', views.InquiryPostHtml.as_view(), name='book_inquiry'),
    # path('books/inquiry/complete/', views.InquiryPostCompleteHtml.as_view(), name='book_inquiry_complete'),

    # # FAQ
    # path('books/faq/', views.book_faq, name='book_faq'),
    
    # # 개인정보처리
    # path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
]
