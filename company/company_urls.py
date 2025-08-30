from django.urls import path
from company.company_views import (
    company_list, company_create, company_edit, 
    company_delete, company_detail
)

app_name = 'company'

urlpatterns = [
    path('', company_list, name='company_list'),
    path('create/', company_create, name='company_create'),
    path('<int:pk>/', company_detail, name='company_detail'),
    path('<int:pk>/edit/', company_edit, name='company_edit'),
    path('<int:pk>/delete/', company_delete, name='company_delete'),
] 