# Approval Workflow Module

A comprehensive approval workflow system for Django ERP applications that supports multi-level, conditional, and role-based approvals across business processes.

## Features

### Core Functionality
- **Multi-Level Approvals**: Support for sequential and parallel approval workflows
- **Conditional Logic**: Auto-approval for low-value transactions and escalation for overdue approvals
- **Role-Based Access**: Configurable approver roles and permissions
- **Audit Trail**: Comprehensive logging of all approval actions and decisions
- **Notifications**: Email, SMS, WhatsApp, and in-app notifications
- **Mobile Support**: Responsive design for mobile and tablet devices

### Business Process Integration
- **Purchase Orders**: Approval workflows for procurement processes
- **Invoices**: Multi-level invoice approval with amount thresholds
- **Journal Vouchers**: Financial transaction approvals
- **Leave Requests**: HR leave approval workflows
- **Expense Claims**: Expense approval with receipt validation

## Installation

1. Add `approval_workflow` to your `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'approval_workflow',
]
```

2. Run migrations:
```bash
python manage.py makemigrations approval_workflow
python manage.py migrate
```

3. Add URL patterns to your main `urls.py`:
```python
urlpatterns = [
    # ... other URLs
    path('approval-workflow/', include('approval_workflow.urls', namespace='approval_workflow')),
]
```

## Models

### Core Models

#### WorkflowType
- Defines different types of workflows (e.g., Purchase Orders, Invoices, Leave Requests)
- Configurable auto-approval thresholds and escalation settings

#### WorkflowDefinition
- Defines specific workflow rules and conditions
- Supports sequential, parallel, and hybrid approval types
- Configurable amount thresholds and approval levels

#### WorkflowLevel
- Represents individual approval levels within a workflow
- Configurable approvers, groups, and roles
- Supports sequential and parallel approval types

#### ApprovalRequest
- Individual approval requests submitted by users
- Tracks current status, approvers, and progress
- Links to related documents and business processes

#### WorkflowLevelApproval
- Tracks approvals at each workflow level
- Records approver decisions, comments, and timestamps

#### ApprovalComment
- Comments and notes on approval requests
- Supports internal and public comments

#### ApprovalNotification
- Tracks notifications sent to users
- Supports multiple notification methods (email, SMS, WhatsApp, in-app)

#### ApprovalAuditLog
- Comprehensive audit trail of all approval actions
- Records user actions, timestamps, and IP addresses

## Usage

### Creating Workflow Types

```python
from approval_workflow.models import WorkflowType

# Create a workflow type for purchase orders
workflow_type = WorkflowType.objects.create(
    name='Purchase Orders',
    description='Approval workflow for purchase orders',
    auto_approval_threshold=1000.00,
    max_approval_days=7,
    escalation_enabled=True
)
```

### Defining Workflows

```python
from approval_workflow.models import WorkflowDefinition, WorkflowLevel

# Create workflow definition
workflow_def = WorkflowDefinition.objects.create(
    name='High Value Purchase Approval',
    workflow_type=workflow_type,
    approval_type='sequential',
    min_amount=10000.00,
    max_amount=999999.99,
    approval_levels=3
)

# Create approval levels
level1 = WorkflowLevel.objects.create(
    workflow_definition=workflow_def,
    level_number=1,
    name='Department Head',
    min_approvals_required=1
)
level1.approvers.add(department_head_user)

level2 = WorkflowLevel.objects.create(
    workflow_definition=workflow_def,
    level_number=2,
    name='Finance Manager',
    min_approvals_required=1
)
level2.approvers.add(finance_manager_user)
```

### Creating Approval Requests

```python
from approval_workflow.models import ApprovalRequest

# Create an approval request
request = ApprovalRequest.objects.create(
    workflow_definition=workflow_def,
    requester=user,
    title='Purchase Equipment',
    description='Purchase new laptops for IT department',
    priority='high',
    amount=15000.00,
    document_type='Purchase Order',
    document_id='PO-2024-001'
)
```

### Approving Requests

```python
from approval_workflow.models import WorkflowLevelApproval

# Approve a request
approval = WorkflowLevelApproval.objects.create(
    approval_request=request,
    workflow_level=level1,
    approver=department_head_user,
    status='approved',
    comments='Approved - Budget available'
)
```

## API Endpoints

### Dashboard
- `GET /approval-workflow/` - Main dashboard
- `GET /approval-workflow/api/stats/` - Dashboard statistics

### Workflow Management
- `GET /approval-workflow/workflow-types/` - List workflow types
- `POST /approval-workflow/workflow-types/create/` - Create workflow type
- `GET /approval-workflow/workflow-definitions/` - List workflow definitions
- `POST /approval-workflow/workflow-definitions/create/` - Create workflow definition

### Approval Requests
- `GET /approval-workflow/requests/` - List approval requests
- `POST /approval-workflow/requests/create/` - Create approval request
- `GET /approval-workflow/requests/<id>/` - View request details
- `POST /approval-workflow/requests/<id>/approve/` - Approve/reject request

### User Views
- `GET /approval-workflow/my-approvals/` - User's pending approvals
- `GET /approval-workflow/my-requests/` - User's submitted requests

## Templates

### Main Templates
- `dashboard.html` - Main approval workflow dashboard
- `approval_request_list.html` - List of approval requests
- `approval_request_detail.html` - Detailed view of a request
- `approval_request_form.html` - Create/edit approval request form

### Static Files
- `css/dashboard.css` - Dashboard styling
- `js/dashboard.js` - Dashboard JavaScript functionality

## Configuration

### Settings

Add the following to your `settings.py`:

```python
# Approval Workflow Settings
APPROVAL_WORKFLOW = {
    'DEFAULT_NOTIFICATION_METHOD': 'in_app',  # 'email', 'sms', 'whatsapp', 'in_app'
    'AUTO_ESCALATION_ENABLED': True,
    'ESCALATION_HOURS': 24,
    'MAX_RETRY_ATTEMPTS': 3,
    'EMAIL_TEMPLATES': {
        'approval_required': 'approval_workflow/email/approval_required.html',
        'status_change': 'approval_workflow/email/status_change.html',
    }
}
```

### Permissions

The module uses Django's built-in permission system. Key permissions:

- `approval_workflow.add_workflowtype` - Can create workflow types
- `approval_workflow.change_workflowtype` - Can modify workflow types
- `approval_workflow.add_workflowdefinition` - Can create workflow definitions
- `approval_workflow.add_approvalrequest` - Can create approval requests
- `approval_workflow.change_approvalrequest` - Can modify approval requests

## Customization

### Custom Workflow Types

You can extend the `WorkflowType` model to add custom fields:

```python
from approval_workflow.models import WorkflowType

class CustomWorkflowType(WorkflowType):
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    custom_field = models.CharField(max_length=100)
    
    class Meta:
        proxy = True
```

### Custom Approval Logic

Override the approval logic in your views:

```python
from approval_workflow.views import ApprovalRequestCreateView

class CustomApprovalRequestCreateView(ApprovalRequestCreateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Add custom logic here
        return response
```

## Testing

Run the test suite:

```bash
python manage.py test approval_workflow
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This module is licensed under the MIT License. See LICENSE file for details.
