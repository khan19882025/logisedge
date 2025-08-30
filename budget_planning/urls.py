from django.urls import path
from . import views

app_name = 'budget_planning'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Budget Plans
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<uuid:pk>/', views.budget_detail, name='budget_detail'),
    path('budgets/<uuid:pk>/edit/', views.budget_edit, name='budget_edit'),
    path('budgets/<uuid:pk>/delete/', views.budget_delete, name='budget_delete'),
    path('budgets/<uuid:pk>/approve/', views.budget_approve, name='budget_approve'),
    
    # Budget Items
    path('budgets/<uuid:budget_pk>/items/create/', views.budget_item_create, name='budget_item_create'),
    path('budget-items/<uuid:pk>/edit/', views.budget_item_edit, name='budget_item_edit'),
    path('budget-items/<uuid:pk>/delete/', views.budget_item_delete, name='budget_item_delete'),
    
    # Budget Templates
    path('templates/', views.budget_template_list, name='budget_template_list'),
    path('templates/create/', views.budget_template_create, name='budget_template_create'),
    path('templates/<uuid:pk>/', views.budget_template_detail, name='budget_template_detail'),
    
    # Reports and Imports
    path('import/', views.budget_import, name='budget_import'),
    path('reports/variance/', views.budget_variance_report, name='budget_variance_report'),
    
    # Budget vs Actual Comparison
    path('budget-vs-actual/', views.budget_vs_actual_dashboard, name='budget_vs_actual_dashboard'),
    path('budget-vs-actual/report/', views.budget_vs_actual_report, name='budget_vs_actual_report'),
    path('budget-vs-actual/report/<uuid:pk>/', views.budget_vs_actual_report_detail, name='budget_vs_actual_report_detail'),
    
    # Variance Alerts
    path('variance-alerts/', views.budget_variance_alerts, name='budget_variance_alerts'),
    path('variance-alerts/create/', views.budget_variance_alert_create, name='budget_variance_alert_create'),
    path('variance-alerts/<uuid:pk>/edit/', views.budget_variance_alert_edit, name='budget_variance_alert_edit'),
    
    # Variance Notifications
    path('variance-notifications/', views.budget_variance_notifications, name='budget_variance_notifications'),
    
    # API endpoints
    path('api/cost-centers-by-department/', views.get_cost_centers_by_department, name='get_cost_centers_by_department'),
    path('api/accounts-by-type/', views.get_accounts_by_type, name='get_accounts_by_type'),
    path('api/budget-summary/', views.budget_summary_data, name='budget_summary_data'),
]
