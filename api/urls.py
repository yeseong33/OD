from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    # APIs
    path('user/', views.UserList.as_view(), name='user_list'),
    path('user/<int:pk>', views.UserDetail.as_view(), name='user_detail'),
    path('book/', views.BookList.as_view(), name='book_list'),
    path('book/<int:pk>', views.BookDetail.as_view(), name='book_detail'),
    path('post/', views.PostList.as_view(), name='post_list'),
    path('post/<int:pk>', views.PostDetail.as_view(), name='post_detail'),
    path('comment/', views.CommentList.as_view(), name='comment_list'),
    path('comment/<int:pk>',
         views.CommentDetail.as_view(), name='comment_detail'),
    path('inquiry/', views.InquiryList.as_view(), name='inquiry_list'),
    path('inquiry/<int:pk>',
         views.InquiryDetail.as_view(), name='inquiry_detail'),
    path('faq/', views.FAQList.as_view(), name='faq_list'),
    path('faq/<int:pk>', views.FAQDetail.as_view(), name='faq_detail'),
    path('books/like/', views.BookLikeView.as_view(), name='book_like')
]
