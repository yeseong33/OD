from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path('', views.index, name='user_index'),
    path('login',views.login, name='login'),
    
    path('kakao', views.kakao_login, name='kakao_login'),
    path('kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('google', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),

]
