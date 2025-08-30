from django.urls import path
from . import views

app_name = 'profit_loss_statement'

urlpatterns = [
    path('', views.profit_loss_report, name='profit_loss_report'),
    path('export/', views.export_profit_loss, name='export_profit_loss'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<int:report_id>/delete/', views.delete_report, name='delete_report'),
]