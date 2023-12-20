from django.db import models

from user.models import User


class Voice(models.Model):
    voice_id = models.AutoField(primary_key=True)
    voice_name = models.CharField(max_length=255)
    voice_like = models.IntegerField(default=0)
    voice_path = models.CharField(max_length=255)
    voice_image_path = models.CharField(max_length=255)
    voice_created_date = models.DateTimeField(auto_now_add=True)
    voice_is_public = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    book_title = models.CharField(max_length=255)
    book_genre = models.CharField(max_length=255, default="Others")
    book_image_path = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255)
    book_price = models.IntegerField()
    book_publisher = models.CharField(max_length=255)
    book_publication_date = models.DateField()
    book_content = models.TextField() # 수정...?
    book_description = models.TextField()
    book_likes = models.IntegerField(default=0)
    book_isbn = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
