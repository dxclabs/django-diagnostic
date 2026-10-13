import secrets
from pathlib import Path

DEBUG = True
USE_TZ = True

BASE_DIR = Path(__file__).resolve().parent

# A fresh key per test run: nothing in the tests depends on its value.
SECRET_KEY = secrets.token_urlsafe(50)

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
    "django.contrib.sessions",
    "django.contrib.sites",
    "django_diagnostic",
]

SITE_ID = 1

MIDDLEWARE = ()

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]
