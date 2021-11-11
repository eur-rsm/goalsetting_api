from django.urls import path

from demo import views

urlpatterns = [
    path('messages/', views.sync_messages, name='messages'),
    path('ping/', views.ping, name='ping'),
    path('config/', views.config, name='config'),
]
