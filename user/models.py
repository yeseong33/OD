from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    oauth_provider = models.CharField(max_length=255)
    oauth_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255)
    user_email = models.CharField(max_length=255)
    # user_phone_number = models.CharField(max_length=255)
    user_created_date = models.DateTimeField(auto_now_add=True)
    user_updated_date = models.DateTimeField(auto_now=True)
    user_book_history = ArrayField(models.IntegerField())
    user_favorite_books = ArrayField(
        models.IntegerField(), null=True, blank=True)
    user_favorite_voices = ArrayField(
        models.IntegerField(), null=True, blank=True)


class Subscription(models.Model):
    sub_id = models.AutoField(primary_key=True)
    is_subscribed = models.BooleanField(default=False)
    sub_start_date = models.DateTimeField(null=True, blank=True)
    sub_end_date = models.DateTimeField(null=True, blank=True)
    sub_payment_status = models.CharField(
        max_length=255, null=True, blank=True, default="pending")
    sub_billing_key = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
