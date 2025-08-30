# Port urls
from django.urls import path
from . import views

app_name = 'port'

urlpatterns = [
    path('', views.port_list, name='port_list'),
    path('create/', views.port_create, name='port_create'),
    path('<int:pk>/edit/', views.port_edit, name='port_edit'),
    path('<int:pk>/', views.port_detail, name='port_detail'),
    path('<int:pk>/delete/', views.port_delete, name='port_delete'),
] 