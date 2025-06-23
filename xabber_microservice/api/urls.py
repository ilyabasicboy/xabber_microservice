from django.contrib import admin
from django.urls import path
from xabber_microservice.api.views import WebhookView


urlpatterns = [
    path('webhook/', WebhookView.as_view(), name='webhook'),
]
