from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import (
    WorkflowType, WorkflowDefinition, WorkflowLevel, ApprovalRequest,
    WorkflowLevelApproval, ApprovalComment
)


class ApprovalWorkflowTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create workflow type
        self.workflow_type = WorkflowType.objects.create(
            name='Test Workflow Type',
            description='Test workflow type for testing',
            is_active=True
        )
        
        # Create workflow definition
        self.workflow_definition = WorkflowDefinition.objects.create(
            name='Test Workflow',
            workflow_type=self.workflow_type,
            description='Test workflow for testing',
            approval_type='sequential',
            is_active=True
        )
        
        # Create workflow level
        self.workflow_level = WorkflowLevel.objects.create(
            workflow_definition=self.workflow_definition,
            level_number=1,
            level_type='sequential',
            name='Level 1',
            min_approvals_required=1
        )
        self.workflow_level.approvers.add(self.user2)

    def test_workflow_type_creation(self):
        """Test workflow type creation"""
        workflow_type = WorkflowType.objects.create(
            name='Test Type',
            description='Test description'
        )
        self.assertEqual(workflow_type.name, 'Test Type')
        self.assertTrue(workflow_type.is_active)

    def test_workflow_definition_creation(self):
        """Test workflow definition creation"""
        definition = WorkflowDefinition.objects.create(
            name='Test Definition',
            workflow_type=self.workflow_type,
            description='Test description'
        )
        self.assertEqual(definition.name, 'Test Definition')
        self.assertEqual(definition.workflow_type, self.workflow_type)

    def test_approval_request_creation(self):
        """Test approval request creation"""
        request = ApprovalRequest.objects.create(
            workflow_definition=self.workflow_definition,
            requester=self.user1,
            title='Test Request',
            description='Test description',
            status='pending'
        )
        self.assertEqual(request.title, 'Test Request')
        self.assertEqual(request.requester, self.user1)
        self.assertEqual(request.status, 'pending')

    def test_workflow_level_approval(self):
        """Test workflow level approval"""
        request = ApprovalRequest.objects.create(
            workflow_definition=self.workflow_definition,
            requester=self.user1,
            title='Test Request',
            description='Test description',
            status='pending',
            current_level=self.workflow_level
        )
        request.current_approvers.add(self.user2)
        
        approval = WorkflowLevelApproval.objects.create(
            approval_request=request,
            workflow_level=self.workflow_level,
            approver=self.user2,
            status='approved',
            comments='Approved'
        )
        self.assertEqual(approval.status, 'approved')
        self.assertEqual(approval.approver, self.user2)

    def test_dashboard_view(self):
        """Test dashboard view"""
        self.client.login(username='testuser1', password='testpass123')
        response = self.client.get(reverse('approval_workflow:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'approval_workflow/dashboard.html')

    def test_approval_request_list_view(self):
        """Test approval request list view"""
        self.client.login(username='testuser1', password='testpass123')
        response = self.client.get(reverse('approval_workflow:approval_request_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'approval_workflow/approval_request_list.html')

    def test_create_approval_request(self):
        """Test creating an approval request"""
        self.client.login(username='testuser1', password='testpass123')
        response = self.client.get(reverse('approval_workflow:approval_request_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'approval_workflow/approval_request_form.html')

    def test_workflow_type_list_view(self):
        """Test workflow type list view"""
        self.client.login(username='testuser1', password='testpass123')
        response = self.client.get(reverse('approval_workflow:workflow_type_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'approval_workflow/workflow_type_list.html')

    def test_workflow_definition_list_view(self):
        """Test workflow definition list view"""
        self.client.login(username='testuser1', password='testpass123')
        response = self.client.get(reverse('approval_workflow:workflow_definition_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'approval_workflow/workflow_definition_list.html')
