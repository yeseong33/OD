import os
from dotenv import load_dotenv
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError

load_dotenv()  # 환경 변수를 로드함

# 모든 요청에서 JWT 토큰을 찾아서 검증하고, 유효하다면 사용자 정보를 request.user에 할당


class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.COOKIES.get('jwt')
        if token:
            try:
                user = authenticate(request, token=token)
                if user:
                    request.user = user
            except ExpiredSignatureError:
                # 토큰이 만료된 경우 새 토큰 발급
                user_info = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=[
                                       os.getenv("JWT_ALGORITHM")], options={"verify_exp": False})
                user = get_user_model().objects.get(pk=user_info['user_id'])

                # 새 토큰 생성
                new_token = create_jwt_token(user)

                # 새 토큰을 쿠키에 설정
                response = self.get_response(request)
                response.set_cookie('jwt', new_token)
                return response

        return self.get_response(request)


def create_jwt_token(user):
    payload = {
        'user_id': user.pk,
        'exp': datetime.utcnow() + timedelta(hours=12)  # 만료 시간 설정
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm=os.getenv("JWT_ALGORITHM"))
