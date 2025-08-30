from django.urls import path
from . import views

app_name = 'cost_center_management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<uuid:pk>/update/', views.department_update, name='department_update'),
    path('departments/<uuid:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Cost Center URLs
    path('cost-centers/', views.cost_center_list, name='cost_center_list'),
    path('cost-centers/create/', views.cost_center_create, name='cost_center_create'),
    path('cost-centers/<uuid:pk>/', views.cost_center_detail, name='cost_center_detail'),
    path('cost-centers/<uuid:pk>/update/', views.cost_center_update, name='cost_center_update'),
    path('cost-centers/<uuid:pk>/delete/', views.cost_center_delete, name='cost_center_delete'),
    
    # Cost Center Budget URLs
    path('budgets/', views.cost_center_budget_list, name='cost_center_budget_list'),
    path('budgets/create/', views.cost_center_budget_create, name='cost_center_budget_create'),
    path('budgets/<uuid:pk>/update/', views.cost_center_budget_update, name='cost_center_budget_update'),
    
    # Cost Center Transaction URLs
    path('transactions/', views.cost_center_transaction_list, name='cost_center_transaction_list'),
    path('transactions/create/', views.cost_center_transaction_create, name='cost_center_transaction_create'),
    
    # Report URLs
    path('reports/', views.cost_center_report_list, name='cost_center_report_list'),
    path('reports/create/', views.cost_center_report_create, name='cost_center_report_create'),
    path('reports/<uuid:pk>/', views.cost_center_report_detail, name='cost_center_report_detail'),
    
    # API URLs
    path('api/cost-centers/', views.api_cost_center_data, name='api_cost_center_data'),
    path('api/cost-centers/<uuid:pk>/stats/', views.api_cost_center_stats, name='api_cost_center_stats'),
]
