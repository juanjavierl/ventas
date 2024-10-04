from app.inicio import views
from django.urls import path

urlpatterns = [
    path('', views.inicio, name='inicio'),
    
    path('ver_planes/', views.verPlanes, name='ver_planes'),
]