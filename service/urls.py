from django.urls import path
from .views import (
    service_list, service_create, service_update, 
    service_detail, service_delete, service_price_ajax
)

app_name = 'service'

urlpatterns = [
    path('', service_list, name='service_list'),
    path('create/', service_create, name='service_create'),
    path('<int:pk>/', service_detail, name='service_detail'),
    path('<int:pk>/update/', service_update, name='service_update'),
    path('<int:pk>/delete/', service_delete, name='service_delete'),
    path('<int:pk>/price/', service_price_ajax, name='service_price_ajax'),
] 