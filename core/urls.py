from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('api.urls')),
    path('api/chat/', include('demo.urls')),
    path('api/accounts/', include('django.contrib.auth.urls')),
    path('api/admin/', admin.site.urls),
]
