from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # path('', views.index, name='community_index'),
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),  # http://127.0.0.1:8000/community/books/search
    path('books/search/<int:isbn>/', views.BookCompleteView.as_view(), name='book_complete'), 
]
