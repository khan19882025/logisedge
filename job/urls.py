from django.urls import path
from .views import (
    JobListView, JobDetailView, JobCreateView, JobUpdateView, JobEditView,
    JobDeleteView, JobPrintView, job_quick_view, job_export, get_customer_salesman,
    get_item_data, get_items_list, get_customer_jobs, get_job_details
)

app_name = 'job'

urlpatterns = [
    # CRUD operations
    path('', JobListView.as_view(), name='job_list'),
    path('create/', JobCreateView.as_view(), name='job_create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/edit/', JobUpdateView.as_view(), name='job_update'),
    path('<int:pk>/edit-job/', JobEditView.as_view(), name='job_edit'),
    path('<int:pk>/delete/', JobDeleteView.as_view(), name='job_delete'),
    path('<int:pk>/print/', JobPrintView.as_view(), name='job_print'),
    
    # Additional views
    path('<int:pk>/quick-view/', job_quick_view, name='job_quick_view'),
    path('export/', job_export, name='job_export'),
    path('get-customer-salesman/<int:customer_id>/', get_customer_salesman, name='get_customer_salesman'),
    path('get-item-data/<int:item_id>/', get_item_data, name='get_item_data'),
    path('get-items-list/', get_items_list, name='get_items_list'),
    
    # API endpoints for Cross Stuffing
    path('api/customer/<int:customer_id>/jobs/', get_customer_jobs, name='get_customer_jobs'),
    path('api/<int:pk>/details/', get_job_details, name='get_job_details'),
    
    # Test form

]