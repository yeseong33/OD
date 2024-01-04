from rest_framework import serializers
from .models import FAQ
from community.models import Inquiry


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        
class InquirySerializer(serializers.ModelSerializer):
    inquiry_created_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    class Meta:
        model = Inquiry
        fields = '__all__'