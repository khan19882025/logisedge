from django.urls import path
from . import views

app_name = 'grn'

urlpatterns = [
    # List and search (main landing page)
    path('', views.GRNListView.as_view(), name='grn_list'),
    
    # CRUD operations
    path('create/', views.GRNCreateView.as_view(), name='grn_create'),
    path('<int:pk>/', views.GRNDetailView.as_view(), name='grn_detail'),
    path('<int:pk>/edit/', views.GRNUpdateView.as_view(), name='grn_edit'),
    path('<int:pk>/delete/', views.GRNDeleteView.as_view(), name='grn_delete'),
    
    # Additional operations
    path('<int:pk>/quick-view/', views.grn_quick_view, name='grn_quick_view'),
    path('<int:pk>/duplicate/', views.grn_duplicate, name='grn_duplicate'),
    path('<int:pk>/status-update/', views.grn_status_update, name='grn_status_update'),
    
    # Print and Email operations
    path('<int:pk>/print/summary/', views.grn_print_summary, name='grn_print_summary'),
    path('<int:pk>/print/detailed/', views.grn_print_detailed, name='grn_print_detailed'),
    path('<int:pk>/print/putaways/', views.grn_print_putaways, name='grn_print_putaways'),
    path('<int:pk>/email/', views.grn_email, name='grn_email'),
    
    # AJAX endpoints
    path('get-job-data/<int:job_id>/', views.get_job_data, name='get_job_data'),
    path('get-job-ed-ctnr-data/<int:job_id>/', views.get_job_ed_ctnr_data, name='get_job_ed_ctnr_data'),
    path('get-items/', views.get_items_ajax, name='get_items'),
] 