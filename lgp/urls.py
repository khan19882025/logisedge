from django.urls import path
from . import views

app_name = 'lgp'

urlpatterns = [
    # LGP List and Search
    path('', views.lgp_list, name='lgp_list'),
    path('search/', views.lgp_ajax_search, name='lgp_ajax_search'),
    
    # LGP CRUD Operations
    path('create/', views.lgp_create, name='lgp_create'),
    path('<int:pk>/', views.lgp_detail, name='lgp_detail'),
    path('<int:pk>/details/', views.lgp_details, name='lgp_details'),
    path('<int:pk>/edit/', views.lgp_update, name='lgp_update'),
    
    # LGP Actions
    path('<int:pk>/dispatch/', views.lgp_dispatch, name='lgp_dispatch'),
    path('dispatch/', views.lgp_dispatch_blank, name='lgp_dispatch_blank'),
    path('dispatch/save/', views.lgp_dispatch_save, name='lgp_dispatch_save'),
    path('dispatch/list/', views.lgp_dispatch_list, name='lgp_dispatch_list'),
    path('dispatch/<int:pk>/', views.lgp_dispatch_detail, name='lgp_dispatch_detail'),
    path('dispatch/<int:pk>/delete/', views.lgp_dispatch_delete, name='lgp_dispatch_delete'),
    path('<int:pk>/cancel/', views.lgp_cancel, name='lgp_cancel'),
    path('<int:pk>/print/', views.lgp_print, name='lgp_print'),
]