from django.urls import path
from . import views

app_name = 'accounts_receivable_aging'

urlpatterns = [
    # Main aging report view
    path('', views.aging_report, name='aging_report'),
    
    # Export functionality
    path('export/', views.export_aging_report, name='export_aging_report'),
    
    # Email functionality
    path('email/', views.send_aging_report_email, name='send_aging_report_email'),
    
    # AJAX endpoints
    path('api/summary/', views.get_aging_summary, name='get_aging_summary'),
]