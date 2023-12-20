from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='audiobook_index'),
    path('template', views.template, name='audiobook_template'),
    path('login', views.login, name='login'),
    path('main', views.main, name='main'),
    
    
    
]
