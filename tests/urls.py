# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf.urls import include
from django.urls import path


urlpatterns = [
    path('', include('django_diagnostic.urls', namespace='django_diagnostic')),
]
