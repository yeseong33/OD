import os
from django.contrib.auth.backends import BaseBackend
from .models import User
import jwt
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()  # 환경 변수를 로드함

# BaseBackend를 오버라이딩


class JWTAuthenticationBackend(BaseBackend):

    # JWT 토큰을 해석하여 사용자의 정보를 조회함
    def authenticate(self, request, token=None):
        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=[
                                 os.getenv('JWT_ALGORITHM')])
            user = User.objects.get(user_id=payload['user_id'])
            return user
        except (jwt.DecodeError, User.DoesNotExist):
            return None
