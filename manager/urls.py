from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('book/request/', views.BookRequestListView.as_view(), name='book_request'),
    path('book/register/<int:book_isbn>/', views.BookRegisterView.as_view(), name='book_register'),
    path('book/register/complete/<int:book_isbn>/', views.BookRegisterCompleteView.as_view(), name='book_register_complete'),
]