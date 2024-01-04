from django.urls import reverse
from rest_framework import serializers
from audiobook.models import Book
from community.models import Inquiry


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class InquirySerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()  # get_detail_url() 의 return 값
    user = serializers.SerializerMethodField()  # get_user() 의 return 값

    class Meta:
        model = Inquiry
        fields = '__all__'

    def get_detail_url(self, obj):
        return reverse('manager:inquiry_detail', kwargs={'inquiry_id': obj.inquiry_id})

    def get_user(self, obj):
        return obj.user.nickname
