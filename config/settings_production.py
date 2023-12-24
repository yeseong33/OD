from .settings import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('AWS_DB_NAME'),
        'USER': os.getenv('AWS_DB_USER'),
        'PASSWORD': os.getenv('AWS_DB_PASSWORD'),
        'HOST': os.getenv('AWS_DB_HOST'),
        'PORT': os.getenv('AWS_DB_PORT'),
    }
}
