from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/update/', views.customer_update, name='customer_update'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('<int:pk>/generate-portal-credentials/', views.generate_portal_credentials, name='generate_portal_credentials'),
    path('<int:pk>/toggle-portal-status/', views.toggle_portal_status, name='toggle_portal_status'),
    path('api/<int:pk>/address/', views.get_customer_address, name='get_customer_address'),
] 