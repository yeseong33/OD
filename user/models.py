from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _  # i18n에서 사용하는 gettext 함수의 별칭


# Django에 있는 기존의 User model을 상속받아서 사용함
class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    oauth_provider = models.CharField(max_length=255)
    oauth_identifier = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=20, unique = False)
    user_created_date = models.DateTimeField(auto_now_add=True)
    user_updated_date = models.DateTimeField(auto_now=True)
    user_book_history = ArrayField(models.IntegerField(), null=True)
    user_favorite_books = ArrayField(
        models.IntegerField(), null=True, blank=True)
    user_favorite_voices = ArrayField(
        models.IntegerField(), null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    # related_name 추가
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )


class Subscription(models.Model):
    sub_id = models.AutoField(primary_key=True)
    is_subscribed = models.BooleanField(default=False)
    sub_start_date = models.DateTimeField(null=True, blank=True)
    sub_end_date = models.DateTimeField(null=True, blank=True)
    sub_payment_status = models.CharField(
        max_length=255, null=True, blank=True, default="pending")
    sub_billing_key = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
