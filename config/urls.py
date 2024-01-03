"""
URL configuration for custom_book_reading_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# config/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from config.views import privacy_policy 

urlpatterns = [
    path('', include('audiobook.urls')),
    path('admin/', admin.site.urls),
    path('community/', include('community.urls')),
    path('user/', include('user.urls')),
    path('manager/', include('manager.urls')),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),  # URL 패턴을 추가합니다.
    path('guest/',include('guest.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
