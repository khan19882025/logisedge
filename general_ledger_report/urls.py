from django.urls import path
from . import views

app_name = 'general_ledger_report'

urlpatterns = [
    # Main report views
    path('', views.general_ledger_report_list, name='report_list'),
    path('create/', views.general_ledger_report_create, name='report_create'),
    path('quick/', views.general_ledger_report_quick, name='report_quick'),
    path('<int:pk>/', views.general_ledger_report_detail, name='report_detail'),
    path('<int:pk>/export/', views.general_ledger_report_export, name='report_export'),
    path('<int:pk>/save/', views.general_ledger_report_save, name='report_save'),
    path('<int:pk>/delete/', views.general_ledger_report_delete, name='report_delete'),
    
    # Template views
    path('templates/', views.report_template_list, name='template_list'),
    path('templates/create/', views.report_template_create, name='template_create'),
    path('templates/<int:pk>/use/', views.report_template_use, name='template_use'),
    
    # AJAX endpoints
    path('ajax/accounts/', views.ajax_get_accounts, name='ajax_accounts'),
] 