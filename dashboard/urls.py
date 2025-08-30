from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('all-activities/', views.all_activities, name='all_activities'),
]