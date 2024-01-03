from rest_framework import serializers
from audiobook.models import Book
from community.models import Inquiry
from django.urls import reverse

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class InquirySerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()  # get_detail_url() 의 return 값

    class Meta:
        model = Inquiry
        fields = ['inquiry_id', 'inquiry_category', 'inquiry_title', 'inquiry_content', 'inquiry_response', 'inquiry_is_answered', 'detail_url']

    def get_detail_url(self, obj):
        return reverse('manager:inquiry_detail', kwargs={'inquiry_id': obj.inquiry_id})