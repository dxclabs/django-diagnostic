from django.urls import include, path

urlpatterns = [
    path("", include("django_diagnostic.urls", namespace="django_diagnostic")),
]
