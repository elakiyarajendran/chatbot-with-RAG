"""
Django settings for docuchat_backend project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-docuchat-secret-key-for-development-eval'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'chat_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'docuchat_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'docuchat_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS configurations
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# DocuChat Configuration (SRS 2.5, 6.3, 6.4)
DOCUCHAT_CONFIG = {
    "PRIMARY_MODEL": os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    "FALLBACK_MODELS": ["gemini-3.5-flash", "gemini-3.8-flash"],
    "TEMPERATURE": 0.1,
    "TOP_P": 0.9,
    "MAX_OUTPUT_TOKENS": 1500,
    "FULL_CONTEXT_TOKEN_THRESHOLD": 100000,
    "CHUNK_SIZE": 800,
    "CHUNK_OVERLAP": 120,
    "TOP_K_PASSAGES": 6,
    "HISTORY_TURNS": 10,
    "MAX_FILE_SIZE_MB": 20,
    "MAX_PAGES": 300,
    "MAX_PASTE_CHARS": 100000,
    "MAX_QUESTION_CHARS": 2000,
}
