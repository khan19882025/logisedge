from django.urls import path
from . import views

app_name = 'source_payment_ledger'

urlpatterns = [
    path('', views.source_payment_ledger_report, name='report'),
    path('export/', views.export_source_payment_ledger, name='export'),
]