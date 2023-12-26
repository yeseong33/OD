from rest_framework import serializers
from audiobook.models import Book
from .models import Post, User 

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['post_title', 'post_content']
        
    def save(self, **kwargs):
        # 수정 필요
        # 현재 로그인 유저
        user = User.objects.get(pk=1)
        # 현재 선택된 책
        book = Book.objects.get(pk=1)
        
        self.validated_data['user'] = user
        self.validated_data['book'] = book

        return super().save(**kwargs)