import os
from contextlib import nullcontext

from rest_framework import serializers

from audiobook.models import Book
from .models import Post, User, Comment, Inquiry
from config.settings import AWS_S3_CUSTOM_DOMAIN, MEDIA_URL, FILE_SAVE_POINT, MEDIA_ROOT


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'nickname', 'oauth_provider',
                    'user_profile_path', 'password', 'user_favorite_books', 'user_book_history', 'user_id','username']

        extra_kwargs = {
            'password': {'write_only': True},
        }
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super(UserSerializer, self).create(validated_data)
        if password is not None:
            user.set_password(password)
            
        user.save()
        return user


class PostSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(
        source='user.nickname', read_only=True)
    post_created_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True)
    post_updated_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True, allow_null=True)

    class Meta:
        model = Post
        fields = ['post_id', 'post_title', 'post_content', 'user_id',
                  'user_nickname', 'post_created_date', 'post_updated_date']

    def save(self, **kwargs):
        book_id = self.context.get('book_id')
        user_id = self.context.get('user_id')
        # 현재 로그인 유저
        user = User.objects.get(pk=user_id)
        # 현재 선택된 책
        book = Book.objects.get(pk=book_id)
        self.validated_data['user'] = user
        self.validated_data['book'] = book
        return super().save(**kwargs)

    # def update(self, instance, validated_data):
    #     print('xhdrhk')
    #     print(validated_data, '벨리드')
    #     instance.post_title = validated_data.get('new_title', instance.post_title)
    #     instance.post_content = validated_data.get('new_content', instance.post_content)
    #     instance.save()

    #     return instance

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        # response['book'] = BookSerializer(instance.book).data
        return response


class BookSerializer(serializers.ModelSerializer):
    post_set = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'

    def update(self, instance, validated_data):
        likes = validated_data.get('book_likes')
        instance.book_likes += likes
        instance.save()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['post_set'] = PostSerializer(
            instance.post_set.all(), many=True).data
        return ret


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['comment_id', 'comment_content']

    def save(self, **kwargs):
        post_id = self.context['post_id']
        user_id = self.context['user_id']
        # 현재 로그인 유저
        user = User.objects.get(pk=user_id)
        # 현재 선택된 게시물
        post = Post.objects.get(pk=post_id)
        self.validated_data['user'] = user
        self.validated_data['post'] = post

        return super().save(**kwargs)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        response['post'] = PostSerializer(instance.post).data
        return response


class InquirySerializer(serializers.ModelSerializer):
    inquiry_created_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    class Meta:
        model = Inquiry
        fields = '__all__'