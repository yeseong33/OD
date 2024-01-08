from django.urls import reverse
from rest_framework import serializers
from .models import FAQ
from community.models import Inquiry



class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'