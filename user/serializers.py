from rest_framework import serializers
from .models import User, Subscription

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


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
    
    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)        