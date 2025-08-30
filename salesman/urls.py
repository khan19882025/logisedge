from django.urls import path
from . import views

app_name = 'salesman'

urlpatterns = [
    path('', views.salesman_list, name='salesman_list'),
    path('create/', views.salesman_create, name='salesman_create'),
    path('<int:pk>/', views.salesman_detail, name='salesman_detail'),
    path('<int:pk>/update/', views.salesman_update, name='salesman_update'),
    path('<int:pk>/delete/', views.salesman_delete, name='salesman_delete'),
] 