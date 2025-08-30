from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import uuid
from datetime import timedelta

from .models import (
    ActivityLog, AuditTrail, SecurityEvent, ComplianceReport,
    RetentionPolicy, AlertRule
)
from .forms import (
    ActivityLogSearchForm, AuditTrailSearchForm, SecurityEventSearchForm,
    ComplianceReportForm, RetentionPolicyForm, AlertRuleForm
)


class ActivityLogsModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_activity_log_creation(self):
        """Test ActivityLog model creation and validation"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='CREATE',
            severity='MEDIUM',
            description='Test activity log',
            module='test_module',
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'CREATE')
        self.assertEqual(log.severity, 'MEDIUM')
        self.assertIsNotNone(log.data_hash)
        self.assertIsNotNone(log.timestamp)
        self.assertTrue(log.created_at <= timezone.now())
        self.assertTrue(log.updated_at <= timezone.now())

    def test_activity_log_data_hash_generation(self):
        """Test that data hash is generated correctly"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='UPDATE',
            severity='LOW',
            description='Test with data',
            before_data={'old': 'value'},
            after_data={'new': 'value'}
        )
        
        # Hash should be generated automatically
        self.assertIsNotNone(log.data_hash)
        self.assertEqual(len(log.data_hash), 64)  # SHA-256 hash length

    def test_audit_trail_creation(self):
        """Test AuditTrail model creation"""
        activity_log = ActivityLog.objects.create(
            user=self.user,
            action_type='UPDATE',
            severity='MEDIUM',
            description='Test audit trail'
        )
        
        audit = AuditTrail.objects.create(
            activity_log=activity_log,
            action_type='UPDATE',
            user=self.user,
            description='Object updated',
            object_type='TestModel',
            object_id='123',
            object_repr='Test Object',
            before_data={'old': 'value'},
            after_data={'new': 'value'},
            change_summary='Value changed from old to new'
        )
        
        self.assertEqual(audit.activity_log, activity_log)
        self.assertEqual(audit.object_type, 'TestModel')
        self.assertEqual(audit.object_id, '123')

    def test_security_event_creation(self):
        """Test SecurityEvent model creation"""
        event = SecurityEvent.objects.create(
            event_type='FAILED_LOGIN',
            severity='HIGH',
            user=self.user,
            description='Multiple failed login attempts',
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            location='Test Location',
            response_required=True
        )
        
        self.assertEqual(event.event_type, 'FAILED_LOGIN')
        self.assertEqual(event.severity, 'HIGH')
        self.assertTrue(event.response_required)
        self.assertEqual(event.status, 'OPEN')

    def test_compliance_report_creation(self):
        """Test ComplianceReport model creation"""
        report = ComplianceReport.objects.create(
            report_type='MONTHLY',
            period_start=timezone.now().date(),
            period_end=(timezone.now() + timedelta(days=30)).date(),
            description='Monthly compliance report',
            generated_by=self.admin_user,
            report_data={'data': 'test'},
            summary='Test summary',
            recommendations='Test recommendations'
        )
        
        self.assertEqual(report.report_type, 'MONTHLY')
        self.assertEqual(report.generated_by, self.admin_user)
        self.assertEqual(report.status, 'DRAFT')

    def test_retention_policy_creation(self):
        """Test RetentionPolicy model creation"""
        policy = RetentionPolicy.objects.create(
            name='Test Policy',
            description='Test retention policy',
            data_type='ACTIVITY_LOGS',
            retention_period=365,
            retention_unit='DAYS',
            archive_enabled=True,
            encryption_required=True,
            compression_enabled=False,
            is_active=True
        )
        
        self.assertEqual(policy.name, 'Test Policy')
        self.assertEqual(policy.retention_period, 365)
        self.assertEqual(policy.retention_unit, 'DAYS')
        self.assertTrue(policy.archive_enabled)
        self.assertTrue(policy.encryption_required)

    def test_alert_rule_creation(self):
        """Test AlertRule model creation"""
        rule = AlertRule.objects.create(
            name='Test Rule',
            description='Test alert rule',
            rule_type='THRESHOLD',
            severity='MEDIUM',
            conditions={'field': 'action_type', 'operator': 'equals', 'value': 'DELETE'},
            threshold=5,
            time_window=3600,
            email_enabled=True,
            sms_enabled=False,
            webhook_enabled=False,
            is_active=True
        )
        
        self.assertEqual(rule.name, 'Test Rule')
        self.assertEqual(rule.rule_type, 'THRESHOLD')
        self.assertEqual(rule.threshold, 5)
        self.assertTrue(rule.email_enabled)
        self.assertFalse(rule.sms_enabled)

    def test_model_string_representations(self):
        """Test model string representations"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='CREATE',
            severity='LOW',
            description='Test log'
        )
        
        self.assertIn(str(self.user.username), str(log))
        self.assertIn('CREATE', str(log))

    def test_model_validation(self):
        """Test model validation"""
        # Test invalid action type
        with self.assertRaises(ValidationError):
            log = ActivityLog(
                user=self.user,
                action_type='INVALID_TYPE',
                severity='LOW',
                description='Test'
            )
            log.full_clean()

        # Test invalid severity
        with self.assertRaises(ValidationError):
            log = ActivityLog(
                user=self.user,
                action_type='CREATE',
                severity='INVALID_SEVERITY',
                description='Test'
            )
            log.full_clean()


class ActivityLogsFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_activity_log_search_form_valid(self):
        """Test ActivityLogSearchForm with valid data"""
        form_data = {
            'search': 'test search',
            'action_type': 'CREATE',
            'severity': 'MEDIUM',
            'user': self.user.id,
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        form = ActivityLogSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_activity_log_search_form_invalid_dates(self):
        """Test ActivityLogSearchForm with invalid date range"""
        form_data = {
            'date_from': '2024-12-31',
            'date_to': '2024-01-01'  # End date before start date
        }
        form = ActivityLogSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_to', form.errors)

    def test_compliance_report_form_valid(self):
        """Test ComplianceReportForm with valid data"""
        form_data = {
            'report_type': 'MONTHLY',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'description': 'Test report',
            'summary': 'Test summary',
            'recommendations': 'Test recommendations'
        }
        form = ComplianceReportForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_retention_policy_form_valid(self):
        """Test RetentionPolicyForm with valid data"""
        form_data = {
            'name': 'Test Policy',
            'description': 'Test description',
            'data_type': 'ACTIVITY_LOGS',
            'retention_period': 365,
            'retention_unit': 'DAYS',
            'archive_enabled': True,
            'encryption_required': False,
            'compression_enabled': True,
            'is_active': True
        }
        form = RetentionPolicyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_alert_rule_form_valid(self):
        """Test AlertRuleForm with valid data"""
        form_data = {
            'name': 'Test Rule',
            'description': 'Test description',
            'rule_type': 'THRESHOLD',
            'severity': 'MEDIUM',
            'threshold': 5,
            'time_window': 3600,
            'email_enabled': True,
            'sms_enabled': False,
            'webhook_enabled': False,
            'is_active': True
        }
        form = AlertRuleForm(data=form_data)
        self.assertTrue(form.is_valid())


class ActivityLogsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test data
        self.activity_log = ActivityLog.objects.create(
            user=self.user,
            action_type='CREATE',
            severity='MEDIUM',
            description='Test activity log'
        )

    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('activity_logs:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/dashboard.html')

    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view redirects unauthenticated users"""
        response = self.client.get(reverse('activity_logs:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_activity_log_list_view(self):
        """Test activity log list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('activity_logs:activity_log_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/activity_log_list.html')
        self.assertContains(response, 'Test activity log')

    def test_activity_log_detail_view(self):
        """Test activity log detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('activity_logs:activity_log_detail', args=[self.activity_log.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/activity_log_detail.html')

    def test_activity_log_create_view(self):
        """Test activity log create view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('activity_logs:activity_log_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/activity_log_form.html')

    def test_activity_log_update_view(self):
        """Test activity log update view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('activity_logs:activity_log_update', args=[self.activity_log.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/activity_log_form.html')

    def test_activity_log_delete_view(self):
        """Test activity log delete view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('activity_logs:activity_log_delete', args=[self.activity_log.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_logs/activity_log_confirm_delete.html')

    def test_activity_log_export_view(self):
        """Test activity log export view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test CSV export
        response = self.client.get(
            reverse('activity_logs:activity_log_export_csv')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Test JSON export
        response = self.client.get(
            reverse('activity_logs:activity_log_export_json')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_chart_data_views(self):
        """Test chart data AJAX views"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test activity log chart data
        response = self.client.get(reverse('activity_logs:activity_log_chart_data'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('data', data)
        
        # Test security event chart data
        response = self.client.get(reverse('activity_logs:security_event_chart_data'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('data', data)

    def test_search_functionality(self):
        """Test search and filter functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test search by description
        response = self.client.get(
            reverse('activity_logs:activity_log_list') + '?search=Test'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test activity log')
        
        # Test filter by action type
        response = self.client.get(
            reverse('activity_logs:activity_log_list') + '?action_type=CREATE'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test activity log')
        
        # Test filter by severity
        response = self.client.get(
            reverse('activity_logs:activity_log_list') + '?severity=MEDIUM'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test activity log')

    def test_pagination(self):
        """Test pagination functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create multiple logs to test pagination
        for i in range(25):
            ActivityLog.objects.create(
                user=self.user,
                action_type='CREATE',
                severity='LOW',
                description=f'Test log {i}'
            )
        
        # Test first page
        response = self.client.get(reverse('activity_logs:activity_log_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test second page
        response = self.client.get(
            reverse('activity_logs:activity_log_list') + '?page=2'
        )
        self.assertEqual(response.status_code, 200)


class ActivityLogsIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_complete_workflow(self):
        """Test complete activity logging workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Create activity log
        log_data = {
            'action_type': 'CREATE',
            'severity': 'MEDIUM',
            'description': 'Integration test log',
            'module': 'test_module',
            'ip_address': '127.0.0.1'
        }
        
        response = self.client.post(
            reverse('activity_logs:activity_log_create'),
            data=log_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # 2. Verify log was created
        log = ActivityLog.objects.get(description='Integration test log')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'CREATE')
        
        # 3. View the log
        response = self.client.get(
            reverse('activity_logs:activity_log_detail', args=[log.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration test log')
        
        # 4. Update the log
        update_data = {
            'action_type': 'UPDATE',
            'severity': 'HIGH',
            'description': 'Updated integration test log',
            'module': 'test_module',
            'ip_address': '127.0.0.1'
        }
        
        response = self.client.post(
            reverse('activity_logs:activity_log_update', args=[log.pk]),
            data=update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Verify update
        log.refresh_from_db()
        self.assertEqual(log.action_type, 'UPDATE')
        self.assertEqual(log.severity, 'HIGH')
        
        # 6. Export logs
        response = self.client.get(
            reverse('activity_logs:activity_log_export_csv')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_security_event_workflow(self):
        """Test security event creation and response workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create security event
        event_data = {
            'event_type': 'FAILED_LOGIN',
            'severity': 'HIGH',
            'description': 'Test security event',
            'ip_address': '192.168.1.1',
            'response_required': True
        }
        
        response = self.client.post(
            reverse('activity_logs:security_event_create'),
            data=event_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify event was created
        event = SecurityEvent.objects.get(description='Test security event')
        self.assertEqual(event.event_type, 'FAILED_LOGIN')
        self.assertTrue(event.response_required)
        
        # Respond to event
        response_data = {
            'response_notes': 'Event investigated and resolved',
            'status': 'RESOLVED'
        }
        
        response = self.client.post(
            reverse('activity_logs:security_event_response', args=[event.pk]),
            data=response_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify response
        event.refresh_from_db()
        self.assertEqual(event.status, 'RESOLVED')
        self.assertFalse(event.response_required)


class ActivityLogsPerformanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create bulk test data
        self.create_bulk_data()

    def create_bulk_data(self):
        """Create bulk test data for performance testing"""
        logs = []
        for i in range(1000):
            log = ActivityLog(
                user=self.user,
                action_type='CREATE',
                severity='LOW',
                description=f'Bulk test log {i}',
                module='test_module',
                ip_address='127.0.0.1'
            )
            logs.append(log)
        
        ActivityLog.objects.bulk_create(logs)

    def test_bulk_creation_performance(self):
        """Test performance of bulk log creation"""
        import time
        
        start_time = time.time()
        
        logs = []
        for i in range(100):
            log = ActivityLog(
                user=self.user,
                action_type='UPDATE',
                severity='MEDIUM',
                description=f'Performance test log {i}',
                module='test_module'
            )
            logs.append(log)
        
        ActivityLog.objects.bulk_create(logs)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(creation_time, 1.0)

    def test_search_performance(self):
        """Test performance of search queries"""
        import time
        
        start_time = time.time()
        
        # Perform search query
        logs = ActivityLog.objects.filter(
            description__icontains='Bulk test log'
        ).select_related('user')[:100]
        
        end_time = time.time()
        search_time = end_time - start_time
        
        # Should complete in reasonable time (less than 0.1 seconds)
        self.assertLess(search_time, 0.1)
        self.assertEqual(len(logs), 100)

    def test_export_performance(self):
        """Test performance of export operations"""
        import time
        
        start_time = time.time()
        
        # Export all logs
        logs = ActivityLog.objects.all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should complete in reasonable time
        self.assertLess(query_time, 0.1)
        self.assertEqual(logs.count(), 1000)
