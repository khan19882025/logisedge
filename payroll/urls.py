from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Dashboard
    path('', views.payroll_dashboard, name='dashboard'),
    
    # Salary Structure Management
    path('salary-structure/', views.salary_structure_list, name='salary_structure_list'),
    path('salary-structure/create/', views.salary_structure_create, name='salary_structure_create'),
    path('salary-structure/<int:structure_id>/edit/', views.salary_structure_edit, name='salary_structure_edit'),
    
    # Employee Salary Management
    path('employee-salary/', views.employee_salary_list, name='employee_salary_list'),
    path('employee-salary/create/', views.employee_salary_create, name='employee_salary_create'),
    path('employee-salary/<int:salary_id>/edit/', views.employee_salary_edit, name='employee_salary_edit'),
    
    # Bank Account Management
    path('bank-account/', views.bank_account_list, name='bank_account_list'),
    path('bank-account/create/', views.bank_account_create, name='bank_account_create'),
    path('bank-account/<int:account_id>/edit/', views.bank_account_edit, name='bank_account_edit'),
    
    # Payroll Period Management
    path('period/', views.payroll_period_list, name='payroll_period_list'),
    path('period/create/', views.payroll_period_create, name='payroll_period_create'),
    
    # Payroll Processing
    path('period/<int:period_id>/process/', views.payroll_process, name='payroll_process'),
    path('period/<int:period_id>/records/', views.payroll_record_list, name='payroll_record_list'),
    path('record/<int:record_id>/edit/', views.payroll_record_edit, name='payroll_record_edit'),
    path('record/<int:record_id>/approve/', views.payroll_approve, name='payroll_approve'),
    
    # Payslip Management
    path('payslip/<int:record_id>/generate/', views.payslip_generate, name='payslip_generate'),
    path('payslip/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    
    # WPS Management
    path('wps/', views.wps_list, name='wps_list'),
    path('wps/export/', views.wps_export, name='wps_export'),
    
    # End of Service Benefits
    path('eosb/', views.eosb_list, name='eosb_list'),
    path('eosb/calculate/', views.eosb_calculate, name='eosb_calculate'),
    path('eosb/<int:eosb_id>/', views.eosb_detail, name='eosb_detail'),
    
    # Loan Management
    path('loan/', views.loan_list, name='loan_list'),
    path('loan/create/', views.loan_create, name='loan_create'),
    path('loan/<int:loan_id>/edit/', views.loan_edit, name='loan_edit'),
    
    # Advance Management
    path('advance/', views.advance_list, name='advance_list'),
    path('advance/create/', views.advance_create, name='advance_create'),
    path('advance/<int:advance_id>/edit/', views.advance_edit, name='advance_edit'),
    path('advance/<int:advance_id>/approve/', views.advance_approve, name='advance_approve'),
    
    # Reports
    path('reports/', views.payroll_reports, name='reports'),
] 