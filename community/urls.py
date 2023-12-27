from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # 토론방
    path('books/share/', views.BookShareContentList.as_view(), name='book_share'),
    path('books/share/content/<int:book_id>', views.BookShareContent.as_view(), name='book_share_content'),
    path('books/share/content/post/', views.BookShareContentPost.as_view(), name='book_share_content_post'),
    path('books/share/content/post/detail/<int:post_id>', views.BookShareContentPostDetail.as_view(), name='book_share_content_post_detail'),
    path('books/share/content/post/detail/comment/', views.BookShareContentPostComment.as_view(), name='book_share_content_post_detail_comment'),



    # 신규 도서 신청
    # http://127.0.0.1:8000/community/books/search
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    path('books/search/<int:isbn>/',
         views.BookCompleteView.as_view(), name='book_complete'),

    # 1:1 문의
    path('books/inquiry/', views.book_inquiry, name='book_inquiry'),

    # FAQ
    path('books/faq/', views.book_faq, name='book_faq'),
]
