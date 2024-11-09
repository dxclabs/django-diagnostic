from django.urls import path

from . import views

app_name = "django_diagnostic"

urlpatterns = [
    # Screens
    path(
        "<slug:app_name>/<slug:slug>/",
        views.DispatcherView.as_view(),
        name="dispatcher",
    ),
    # path('<slug:app_name>/', views.DispatcherView.as_view(), name='dispatcher'),
    path("", views.IndexView.as_view(), name="index"),
    # Reports
    # Modals
    # Panels
    # Actions
    # APIs
    # Utils
    # Diagnostic
    # Deprecated
]
