from rest_framework import serializers
from audiobook.models import Book
from user.models import Subscription

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'