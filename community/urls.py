from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # 토론방
    path('books/share/', views.book_share, name='book_share'),

    # 신규 도서 신청
    # http://127.0.0.1:8000/community/books/search
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    path('books/search/<int:isbn>/', views.BookCompleteView.as_view(), name='book_complete'),

    # 1:1 문의
    path('books/inquiry/', views.book_inquiry, name='book_inquiry'),

    # FAQ
    path('books/faq/', views.book_faq, name='book_faq'),
]
