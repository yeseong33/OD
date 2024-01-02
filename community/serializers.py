from contextlib import nullcontext
from rest_framework import serializers
from audiobook.models import Book
from .models import Post, User, Comment, Inquiry

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['post_id', 'post_title', 'post_content']
        
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
        ret['post_set'] = list(instance.post_set.values())
        for post in ret['post_set']:
            post['post_created_date'] = post['post_created_date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            post['post_updated_date'] = post['post_updated_date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ') if post['post_updated_date'] else "None"
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
    class Meta: 
        model = Inquiry
        fields = '__all__'