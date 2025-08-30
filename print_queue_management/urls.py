from django.urls import path
from . import views

app_name = 'print_queue_management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Printer Management
    path('printers/', views.printer_list, name='printer_list'),
    path('printers/create/', views.printer_create, name='printer_create'),
    path('printers/<uuid:pk>/', views.printer_detail, name='printer_detail'),
    path('printers/<uuid:pk>/edit/', views.printer_update, name='printer_update'),
    path('printers/<uuid:pk>/delete/', views.printer_delete, name='printer_delete'),
    
    # Printer Group Management
    path('printer-groups/', views.printer_group_list, name='printer_group_list'),
    path('printer-groups/create/', views.printer_group_create, name='printer_group_create'),
    path('printer-groups/<uuid:pk>/', views.printer_group_detail, name='printer_group_detail'),
    path('printer-groups/<uuid:pk>/edit/', views.printer_group_update, name='printer_group_update'),
    
    # Print Template Management
    path('templates/', views.print_template_list, name='print_template_list'),
    path('templates/create/', views.print_template_create, name='print_template_create'),
    path('templates/<uuid:pk>/', views.print_template_detail, name='print_template_detail'),
    path('templates/<uuid:pk>/edit/', views.print_template_update, name='print_template_update'),
    
    # Auto-Print Rule Management
    path('rules/', views.auto_print_rule_list, name='auto_print_rule_list'),
    path('rules/create/', views.auto_print_rule_create, name='auto_print_rule_create'),
    path('rules/<uuid:pk>/', views.auto_print_rule_detail, name='auto_print_rule_detail'),
    path('rules/<uuid:pk>/edit/', views.auto_print_rule_update, name='auto_print_rule_update'),
    
    # Print Job Management
    path('jobs/', views.print_job_list, name='print_job_list'),
    path('jobs/create/', views.print_job_create, name='print_job_create'),
    path('jobs/<uuid:pk>/', views.print_job_detail, name='print_job_detail'),
    path('jobs/<uuid:pk>/action/', views.print_job_action, name='print_job_action'),
    
    # Import/Export
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    
    # API Endpoints
    path('api/printer/<uuid:pk>/status/', views.printer_status_api, name='printer_status_api'),
    path('api/queue/stats/', views.queue_stats_api, name='queue_stats_api'),
]
