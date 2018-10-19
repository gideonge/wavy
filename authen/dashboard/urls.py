from django.urls import path, include
from django.conf.urls import url
from . import views

urlpatterns = [
    path('login/', views.authen_login),
    path('', views.index),
    path('test/', views.handle_post),
    path('stock/', views.handle_stock),
    path('logout/', views.logout_view),
    url(r'^index/$', views.index, name='index'),
    url(r'^stock-data/$', views.candle_stock, name='candle_stock'),
    url(r'^finance/$', views.financial_date, name='finance_data')
]