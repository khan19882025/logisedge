from django.urls import path
from . import views

app_name = 'activity_logs'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    
    # Activity Log URLs
    path('activity-logs/', views.ActivityLogListView.as_view(), name='activity_log_list'),
    path('activity-logs/<uuid:pk>/', views.ActivityLogDetailView.as_view(), name='activity_log_detail'),
    path('activity-logs/create/', views.ActivityLogCreateView.as_view(), name='activity_log_create'),
    path('activity-logs/<uuid:pk>/update/', views.ActivityLogUpdateView.as_view(), name='activity_log_update'),
    path('activity-logs/<uuid:pk>/delete/', views.ActivityLogDeleteView.as_view(), name='activity_log_delete'),
    
    path('activity-logs/export/csv/', views.activity_log_export_csv, name='activity_log_export_csv'),
    path('activity-logs/export/json/', views.activity_log_export_json, name='activity_log_export_json'),
    
    # Audit Trail URLs
    path('audit-trails/', views.AuditTrailListView.as_view(), name='audit_trail_list'),
    path('audit-trails/<uuid:pk>/', views.AuditTrailDetailView.as_view(), name='audit_trail_detail'),
    path('audit-trails/create/', views.AuditTrailCreateView.as_view(), name='audit_trail_create'),
    path('audit-trails/<uuid:pk>/update/', views.AuditTrailUpdateView.as_view(), name='audit_trail_update'),
    path('audit-trails/<uuid:pk>/delete/', views.AuditTrailDeleteView.as_view(), name='audit_trail_delete'),
    
    # Security Event URLs
    path('security-events/', views.SecurityEventListView.as_view(), name='security_event_list'),
    path('security-events/<uuid:pk>/', views.SecurityEventDetailView.as_view(), name='security_event_detail'),
    path('security-events/create/', views.SecurityEventCreateView.as_view(), name='security_event_create'),
    path('security-events/<uuid:pk>/update/', views.SecurityEventUpdateView.as_view(), name='security_event_update'),
    path('security-events/<uuid:pk>/delete/', views.SecurityEventDeleteView.as_view(), name='security_event_delete'),
    path('security-events/<uuid:pk>/response/', views.security_event_response, name='security_event_response'),
    
    # Compliance Report URLs
    path('compliance-reports/', views.ComplianceReportListView.as_view(), name='compliance_report_list'),
    path('compliance-reports/<uuid:pk>/', views.ComplianceReportDetailView.as_view(), name='compliance_report_detail'),
    path('compliance-reports/create/', views.ComplianceReportCreateView.as_view(), name='compliance_report_create'),
    path('compliance-reports/<uuid:pk>/update/', views.ComplianceReportUpdateView.as_view(), name='compliance_report_update'),
    path('compliance-reports/<uuid:pk>/delete/', views.ComplianceReportDeleteView.as_view(), name='compliance_report_delete'),
    
    # Retention Policy URLs
    path('retention-policies/', views.RetentionPolicyListView.as_view(), name='retention_policy_list'),
    path('retention-policies/<uuid:pk>/', views.RetentionPolicyDetailView.as_view(), name='retention_policy_detail'),
    path('retention-policies/create/', views.RetentionPolicyCreateView.as_view(), name='retention_policy_create'),
    path('retention-policies/<uuid:pk>/update/', views.RetentionPolicyUpdateView.as_view(), name='retention_policy_update'),
    path('retention-policies/<uuid:pk>/delete/', views.RetentionPolicyDeleteView.as_view(), name='retention_policy_delete'),
    
    # Alert Rule URLs
    path('alert-rules/', views.AlertRuleListView.as_view(), name='alert_rule_list'),
    path('alert-rules/<uuid:pk>/', views.AlertRuleDetailView.as_view(), name='alert_rule_detail'),
    path('alert-rules/create/', views.AlertRuleCreateView.as_view(), name='alert_rule_create'),
    path('alert-rules/<uuid:pk>/update/', views.AlertRuleUpdateView.as_view(), name='alert_rule_update'),
    path('alert-rules/<uuid:pk>/delete/', views.AlertRuleDeleteView.as_view(), name='alert_rule_delete'),
    
    # Utility URLs
    path('object-audit-trail/<str:content_type_id>/<int:object_id>/', views.object_audit_trail, name='object_audit_trail'),
    path('user-activity-summary/<int:user_id>/', views.user_activity_summary, name='user_activity_summary'),
    
    # AJAX endpoints for charts and data
    path('ajax/activity-log-chart-data/', views.activity_log_chart_data, name='activity_log_chart_data'),
    path('ajax/security-event-chart-data/', views.security_event_chart_data, name='security_event_chart_data'),
]
