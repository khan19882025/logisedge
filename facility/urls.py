from django.urls import path
from . import views

app_name = 'facility'

urlpatterns = [
    # Facility URLs
    path('', views.facility_list, name='facility_list'),
    path('create/', views.facility_create, name='facility_create'),
    path('<int:pk>/', views.facility_detail, name='facility_detail'),
    path('<int:pk>/update/', views.facility_update, name='facility_update'),
    path('<int:pk>/delete/', views.facility_delete, name='facility_delete'),
    path('<int:pk>/quick-view/', views.facility_quick_view, name='facility_quick_view'),
    path('<int:pk>/toggle-status/', views.facility_status_toggle, name='facility_status_toggle'),
    path('<int:facility_pk>/locations/', views.facility_locations, name='facility_locations'),
    path('export/', views.facility_export, name='facility_export'),
    
    # Location URLs
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('locations/<int:pk>/update/', views.location_update, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),
    path('locations/<int:pk>/quick-view/', views.location_quick_view, name='location_quick_view'),
    
    # Class-based views (alternative)
    # path('', views.FacilityListView.as_view(), name='facility_list'),
    # path('create/', views.FacilityCreateView.as_view(), name='facility_create'),
    # path('<int:pk>/', views.FacilityDetailView.as_view(), name='facility_detail'),
    # path('<int:pk>/update/', views.FacilityUpdateView.as_view(), name='facility_update'),
    # path('<int:pk>/delete/', views.FacilityDeleteView.as_view(), name='facility_delete'),
] 