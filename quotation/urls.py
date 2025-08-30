from django.urls import path
from .views import (
    quotation_list, quotation_create, quotation_update, quotation_detail,
    quotation_delete, quotation_status_update, quotation_duplicate, print_quotation
)

app_name = 'quotation'

urlpatterns = [
    # Main quotation views
    path('', quotation_list, name='quotation_list'),
    path('create/', quotation_create, name='quotation_create'),
    path('<int:pk>/', quotation_detail, name='quotation_detail'),
    path('<int:pk>/edit/', quotation_update, name='quotation_update'),
    path('<int:pk>/delete/', quotation_delete, name='quotation_delete'),
    path('<int:pk>/duplicate/', quotation_duplicate, name='quotation_duplicate'),
    path('<int:pk>/print/', print_quotation, name='print_quotation'),
    
    # AJAX endpoints
    path('<int:pk>/status/', quotation_status_update, name='quotation_status_update'),
] 