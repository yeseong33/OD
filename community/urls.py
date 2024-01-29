from django.urls import path, include
from . import views

app_name = 'community'

urlpatterns = [

    # html render
    # 토론
    path('books/share/', views.BookShareHtml.as_view(), name='book_share'),
    path('books/share/content/<int:pk>',
         views.BookShareContentHtml.as_view(), name='book_share_content'),
    path('books/share/content/post/', views.BookShareContentPostHtml.as_view(),
         name='book_share_content_post'),
    path('books/share/content/post/detail/<int:pk>',
         views.BookShareContentPostDetailHtml.as_view(), name='book_share_content_post_detail'),

    # 신규 도서 신청
    # http://127.0.0.1:8000/community/books/search
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    path('api/books/search/<str:isbn>/',
         views.BookRequestAPI.as_view(), name='book_complete'),

    # 1:1 문의
    path('books/inquiry/', views.InquiryPostHtml.as_view(), name='book_inquiry'),
    path('books/inquiry/complete/', views.InquiryPostCompleteHtml.as_view(),
         name='book_inquiry_complete'),

    # FAQ
    path('books/faq/', views.FAQHtml.as_view(), name='book_faq'),

]
