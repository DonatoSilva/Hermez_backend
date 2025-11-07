from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('user/', include('users.urls')),
    path('deliveries/', include('deliveries.urls')),
]
