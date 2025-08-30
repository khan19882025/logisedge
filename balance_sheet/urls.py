from django.urls import path
from . import views

app_name = 'balance_sheet'

urlpatterns = [
    path('', views.balance_sheet_report, name='balance_sheet_report'),
    path('export/', views.export_balance_sheet, name='export_balance_sheet'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
] 