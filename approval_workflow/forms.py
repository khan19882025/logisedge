from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    WorkflowType, WorkflowDefinition, WorkflowLevel, ApprovalRequest,
    WorkflowLevelApproval, ApprovalComment, ApprovalNotification,
    WorkflowTemplate
)


class WorkflowTypeForm(forms.ModelForm):
    """Form for creating and editing workflow types"""
    
    class Meta:
        model = WorkflowType
        fields = [
            'name', 'description', 'is_active', 'requires_approval',
            'auto_approval_threshold', 'max_approval_days',
            'escalation_enabled', 'notification_enabled'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'auto_approval_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_approval_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if WorkflowType.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError("A workflow type with this name already exists.")
        return name


class WorkflowDefinitionForm(forms.ModelForm):
    """Form for creating and editing workflow definitions"""
    
    class Meta:
        model = WorkflowDefinition
        fields = [
            'name', 'workflow_type', 'description', 'approval_type',
            'is_active', 'condition_type', 'condition_value',
            'min_amount', 'max_amount', 'approval_levels',
            'auto_approve_if_no_approvers'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'workflow_type': forms.Select(attrs={'class': 'form-control'}),
            'approval_type': forms.Select(attrs={'class': 'form-control'}),
            'condition_type': forms.Select(attrs={'class': 'form-control'}),
            'condition_value': forms.TextInput(attrs={'class': 'form-control'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'approval_levels': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if min_amount and max_amount and min_amount >= max_amount:
            raise ValidationError("Minimum amount must be less than maximum amount.")
        
        return cleaned_data


class WorkflowLevelForm(forms.ModelForm):
    """Form for creating and editing workflow levels"""
    
    class Meta:
        model = WorkflowLevel
        fields = [
            'level_number', 'level_type', 'name', 'description',
            'approvers', 'approver_groups', 'approver_roles',
            'min_approvals_required', 'deadline_hours',
            'can_approve', 'can_reject', 'can_return', 'can_comment',
            'is_active'
        ]
        widgets = {
            'level_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'level_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'approvers': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'approver_groups': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'approver_roles': forms.TextInput(attrs={'class': 'form-control'}),
            'min_approvals_required': forms.NumberInput(attrs={'class': 'form-control'}),
            'deadline_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_level_number(self):
        level_number = self.cleaned_data['level_number']
        workflow_definition = self.instance.workflow_definition if self.instance else None
        
        if workflow_definition:
            if WorkflowLevel.objects.filter(
                workflow_definition=workflow_definition,
                level_number=level_number
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError("A level with this number already exists for this workflow.")
        
        return level_number


class ApprovalRequestForm(forms.ModelForm):
    """Form for creating and editing approval requests"""
    
    class Meta:
        model = ApprovalRequest
        fields = [
            'workflow_definition', 'title', 'description', 'priority',
            'document_type', 'document_id', 'document_reference', 'amount'
        ]
        widgets = {
            'workflow_definition': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'document_type': forms.TextInput(attrs={'class': 'form-control'}),
            'document_id': forms.TextInput(attrs={'class': 'form-control'}),
            'document_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active workflow definitions
        self.fields['workflow_definition'].queryset = WorkflowDefinition.objects.filter(is_active=True)


class ApprovalRequestFilterForm(forms.Form):
    """Form for filtering approval requests"""
    
    STATUS_CHOICES = [('', 'All Status')] + ApprovalRequest.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + ApprovalRequest.PRIORITY_CHOICES
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    workflow_definition = forms.ModelChoiceField(
        queryset=WorkflowDefinition.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    requester = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search requests...'}))


class WorkflowLevelApprovalForm(forms.ModelForm):
    """Form for approval actions"""
    
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('return', 'Return for Revision'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = WorkflowLevelApproval
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your comments...'}),
        }

    def __init__(self, *args, **kwargs):
        self.approval_request = kwargs.pop('approval_request', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.approval_request and self.user:
            # Check user permissions and adjust action choices accordingly
            workflow_level = self.approval_request.current_level
            if workflow_level:
                if not workflow_level.can_approve:
                    self.fields['action'].choices = [choice for choice in self.fields['action'].choices if choice[0] != 'approve']
                if not workflow_level.can_reject:
                    self.fields['action'].choices = [choice for choice in self.fields['action'].choices if choice[0] != 'reject']
                if not workflow_level.can_return:
                    self.fields['action'].choices = [choice for choice in self.fields['action'].choices if choice[0] != 'return']


class ApprovalCommentForm(forms.ModelForm):
    """Form for adding comments to approval requests"""
    
    class Meta:
        model = ApprovalComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your comment...'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WorkflowTemplateForm(forms.ModelForm):
    """Form for creating workflow templates"""
    
    class Meta:
        model = WorkflowTemplate
        fields = ['name', 'description', 'workflow_definition']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'workflow_definition': forms.Select(attrs={'class': 'form-control'}),
        }


class BulkApprovalForm(forms.Form):
    """Form for bulk approval actions"""
    
    approval_ids = forms.CharField(widget=forms.HiddenInput())
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Selected'),
            ('reject', 'Reject Selected'),
            ('return', 'Return Selected'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comments for all selected requests...'}),
        required=False
    )

    def clean_approval_ids(self):
        approval_ids = self.cleaned_data['approval_ids']
        if not approval_ids:
            raise ValidationError("No approvals selected.")
        
        try:
            # Convert comma-separated string to list of integers
            ids = [int(id.strip()) for id in approval_ids.split(',') if id.strip()]
            if not ids:
                raise ValidationError("No valid approval IDs provided.")
            return ids
        except ValueError:
            raise ValidationError("Invalid approval IDs provided.")


class WorkflowLevelAssignForm(forms.Form):
    """Form for assigning approvers to workflow levels"""
    
    approvers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    approver_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    approver_roles = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated role names'})
    )

    def clean(self):
        cleaned_data = super().clean()
        approvers = cleaned_data.get('approvers')
        approver_groups = cleaned_data.get('approver_groups')
        approver_roles = cleaned_data.get('approver_roles')
        
        if not any([approvers.exists() if approvers else False, 
                   approver_groups.exists() if approver_groups else False, 
                   approver_roles.strip() if approver_roles else False]):
            raise ValidationError("At least one approver, group, or role must be specified.")
        
        return cleaned_data


class ApprovalNotificationForm(forms.ModelForm):
    """Form for creating approval notifications"""
    
    class Meta:
        model = ApprovalNotification
        fields = ['notification_type', 'notification_method', 'title', 'message']
        widgets = {
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'notification_method': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
