from django.urls import path
from . import views

app_name = 'bill_of_lading'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # HBL Management
    path('hbl/', views.hbl_list, name='hbl_list'),
    path('hbl/<uuid:hbl_id>/', views.hbl_detail, name='hbl_detail'),
    path('hbl/new/', views.hbl_detail, name='hbl_create'),
    path('hbl/<uuid:hbl_id>/delete/', views.hbl_delete, name='hbl_delete'),
    path('hbl/<uuid:hbl_id>/print/', views.print_hbl, name='print_hbl'),
    path('hbl/<uuid:hbl_id>/charges/', views.hbl_charges, name='hbl_charges'),
    
    # Reports
    path('hbl/report/', views.hbl_report, name='hbl_report'),
    
    # AJAX endpoints
    path('hbl/<uuid:hbl_id>/change-status/', views.change_status, name='change_status'),
    path('add-customer/', views.add_customer, name='add_customer'),
    
    # Export functions
    path('export/excel/', views.export_hbl_excel, name='export_excel'),
    path('export/pdf/', views.export_hbl_pdf, name='export_pdf'),
]
