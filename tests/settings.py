from pathlib import Path

DEBUG = True
USE_TZ = True

BASE_DIR = Path(__file__).resolve().parent

# Throwaway key for the test settings module only -- never used outside pytest.
SECRET_KEY = "7JkxsUpTJsnZfcifb88MzqaHr0VhNYghdidV2fKSsbvS2P4Lmr"  # noqa: S105

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
