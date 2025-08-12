from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    #generar una vista que permita acceder a los diferentes endpoints de la API
    path('', include('users.urls')),
    path('', include('addresses.urls')),
]
