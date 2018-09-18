from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.authen_login),
    path('', views.index),
    path('test/', views.handle_post),
    path('stock/', views.handle_stock),
    path('logout/', views.logout_view)
]