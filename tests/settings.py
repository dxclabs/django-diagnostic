# import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "7JkxsUpTJsnZfcifb88MzqaHr0VhNYghdidV2fKSsbvS2P4Lmr"  # nosec

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django_diagnostic",
]

SITE_ID = 1

MIDDLEWARE = ()
