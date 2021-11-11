from django.urls import path

from . import views

urlpatterns = [
    path('messages/', views.sync_messages, name='messages'),
    path('ping/', views.ping, name='ping'),
    path('config/', views.config, name='config'),
    path('ingress/', views.ingress, name='ingress'),
    path('ingress_task/', views.ingress_task, name='ingress_task'),
    path('get_names/', views.get_names, name='get_names'),

    # TODO Only here for legacy reasons
    path('add_task/', views.ingress_task, name='ingress_task'),
    # TODO Needed?
    path('log/', views.log, name='log'),
]

