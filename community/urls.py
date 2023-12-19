from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # path('', views.index, name='community_index'),
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
]
