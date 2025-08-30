from django.urls import path
from . import views

app_name = 'trial_balance'

urlpatterns = [
    # Main trial balance report generation
    path('', views.trial_balance_report, name='trial_balance_report'),
    
    # Export functionality
    path('export/', views.export_trial_balance, name='export_trial_balance'),
] 