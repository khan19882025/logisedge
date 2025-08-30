from django.urls import path
from . import views

app_name = 'customs_BOE_report'

urlpatterns = [
    path('', views.customs_boe_report, name='report'),
    path('export/excel/', views.export_to_excel, name='export_excel'),
    path('export/pdf/', views.export_to_pdf, name='export_pdf'),
]