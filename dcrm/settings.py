from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-r453f^%@cwj02hv*pss=gkjndq@c^v*+lxvy))uj3^p#o7!yuj")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Allowed hosts for Railway and custom domains
railway_app_url = os.environ.get("RAILWAY_URL", "nurturing-caring-production.up.railway.app")  # Adjust with your Railway URL
ALLOWED_HOSTS = [railway_app_url, "pynnacleproperty.com", "www.pynnacleproperty.com", "127.0.0.1", "localhost"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "website",
    "dal",
    "dal_select2",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dcrm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "dcrm.wsgi.application"

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
        engine='django.db.backends.postgresql_psycopg2'  # Explicit ENGINE for local compatibility
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Create this directory if using custom static files
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For collectstatic

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication redirects
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# CSRF and Fly.io proxy settings
CSRF_TRUSTED_ORIGINS = ['https://pynnacleproperty.com', 'https://pynnaclecrm.fly.dev']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Backblaze B2 integration
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = 'https://s3.eu-central-003.backblazeb2.com'
AWS_STORAGE_BUCKET_NAME = 'pynnacle'
AWS_S3_ACCESS_KEY_ID = os.environ.get('B2_KEY_ID')
AWS_S3_SECRET_ACCESS_KEY = os.environ.get('B2_APPLICATION_KEY')
AWS_S3_FILE_OVERWRITE = False