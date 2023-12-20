from django.contrib import admin
from .models import BookRequest, UserRequestBook

# Register your models here.
admin.site.register(BookRequest)
admin.site.register(UserRequestBook)