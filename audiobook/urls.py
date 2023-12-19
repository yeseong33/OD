from django.urls import path
from . import views

app_name = 'audiobook'

urlpatterns = [
    path('', views.index, name='index'),
    path('template', views.template, name='template'),
    path('custom', views.custom, name='custom'),
]
