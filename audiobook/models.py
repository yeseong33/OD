from django.db import models
from user.models import User
import json


class Voice(models.Model):
    voice_id = models.AutoField(primary_key=True)
    voice_name = models.CharField(max_length=255)
    voice_like = models.IntegerField(default=0)
    voice_path = models.FileField(upload_to='voice_rvcs/', null=True)  # RVC 모델
    voice_image_path = models.ImageField(
        upload_to='voice_images/', blank=True)  # pillow
    voice_sample_path = models.FileField(
        upload_to='voice_sample/', null=True)  # 음성 샘플
    voice_created_date = models.DateTimeField(auto_now_add=True)
    voice_is_public = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.voice_name


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    book_title = models.CharField(max_length=255)
    book_genre = models.CharField(max_length=255, default="Others")
    book_image_path = models.ImageField(
        upload_to='book_images/', blank=True)  # pillow
    book_author = models.CharField(max_length=255)
    book_publisher = models.CharField(max_length=255)
    book_publication_date = models.DateField()
    book_content_path = models.FileField(upload_to='book_contents/', null=True)
    book_description = models.TextField()
    book_likes = models.IntegerField(default=0)
    book_isbn = models.CharField(max_length=255)
    book_view_count = models.JSONField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
