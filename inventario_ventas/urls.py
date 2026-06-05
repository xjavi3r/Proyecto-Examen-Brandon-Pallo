from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("productos.urls")),
    path("api/", include("productos.api_urls")),
]
