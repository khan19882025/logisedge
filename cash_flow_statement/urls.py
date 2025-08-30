from django.urls import path
from . import views

app_name = 'cash_flow_statement'

urlpatterns = [
    # Main report views
    path('', views.cash_flow_statement_list, name='report_list'),
    path('create/', views.cash_flow_statement_create, name='report_create'),
    path('quick/', views.cash_flow_statement_quick, name='report_quick'),
    path('quick/export/', views.quick_report_export, name='quick_export'),
    path('quick/save/', views.quick_report_save, name='quick_save'),
    path('<int:pk>/', views.cash_flow_statement_detail, name='report_detail'),
    path('<int:pk>/export/', views.cash_flow_statement_export, name='report_export'),
    path('<int:pk>/save/', views.cash_flow_statement_save, name='report_save'),
    path('<int:pk>/delete/', views.cash_flow_statement_delete, name='report_delete'),
    
    # Template views
    path('templates/', views.report_template_list, name='template_list'),
    path('templates/create/', views.report_template_create, name='template_create'),
    path('templates/<int:pk>/use/', views.report_template_use, name='template_use'),
    
    # AJAX endpoints
    path('ajax/accounts/', views.ajax_get_accounts, name='ajax_accounts'),
] 