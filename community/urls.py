from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # APIs
    path('book/', views.BookList.as_view(), name='book_list'),  
    path('book/<int:pk>', views.BookDetail.as_view(), name='book_detail'),  
    path('post/', views.PostList.as_view(), name='post_list'),  
    path('post/<int:pk>', views.PostDetail.as_view(), name='post_detail'),  
    path('comment/', views.CommentList.as_view(), name='comment_list'),  
    path('comment/<int:pk>', views.CommentDetail.as_view(), name='comment_detail'),  
    
    # html render
    # 토론
    path('books/share/', views.BookShareHtml.as_view(), name='book_share'),
    path('books/share/content/<int:pk>', views.BookShareContentHtml.as_view(), name='book_share_content'),
    path('books/share/content/post/', views.BookShareContentPostHtml.as_view(), name='book_share_content_post'),
    path('books/share/content/post/detail/<int:pk>', views.BookShareContentPostDetailHtml.as_view(), name='book_share_content_post_detail'),


    # 신규 도서 신청
    # http://127.0.0.1:8000/community/books/search
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    path('books/search/<int:isbn>/', views.BookCompleteView.as_view(), name='book_complete'),

    # 1:1 문의
    path('books/inquiry/', views.book_inquiry, name='book_inquiry'),

    # FAQ
    path('books/faq/', views.book_faq, name='book_faq'),
]
