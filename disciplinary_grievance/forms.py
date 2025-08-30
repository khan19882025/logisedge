from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Grievance, GrievanceCategory, GrievanceAttachment, GrievanceNote,
    DisciplinaryCase, DisciplinaryAction, DisciplinaryActionType,
    DisciplinaryActionDocument, Appeal, EscalationMatrix
)


class GrievanceCategoryForm(forms.ModelForm):
    """Form for creating/editing grievance categories"""
    
    class Meta:
        model = GrievanceCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DisciplinaryActionTypeForm(forms.ModelForm):
    """Form for creating/editing disciplinary action types"""
    
    class Meta:
        model = DisciplinaryActionType
        fields = ['name', 'description', 'severity_level', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter action type name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'severity_level': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GrievanceForm(forms.ModelForm):
    """Form for creating/editing grievances"""
    
    class Meta:
        model = Grievance
        fields = [
            'title', 'description', 'category', 'priority', 'employee',
            'is_anonymous', 'incident_date', 'incident_location', 'witnesses',
            'assigned_to', 'is_confidential'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter grievance title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the grievance in detail'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'incident_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where did the incident occur?'}),
            'witnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Names and contact details of witnesses'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active categories
        self.fields['category'].queryset = GrievanceCategory.objects.filter(is_active=True)
        # Filter active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False

    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now().date():
            raise ValidationError("Incident date cannot be in the future.")
        return incident_date


class GrievanceAttachmentForm(forms.ModelForm):
    """Form for uploading grievance attachments"""
    
    class Meta:
        model = GrievanceAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of the file'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be less than 10MB.")
            
            # Check file type
            allowed_types = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_types:
                raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
        
        return file


class GrievanceNoteForm(forms.ModelForm):
    """Form for adding notes to grievances"""
    
    class Meta:
        model = GrievanceNote
        fields = ['note', 'is_internal']
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your note here...'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DisciplinaryCaseForm(forms.ModelForm):
    """Form for creating/editing disciplinary cases"""
    
    class Meta:
        model = DisciplinaryCase
        fields = [
            'title', 'description', 'severity', 'employee', 'incident_date',
            'incident_time', 'incident_location', 'policy_violation',
            'witnesses', 'evidence_description', 'assigned_investigator',
            'committee_members', 'related_grievance', 'is_confidential'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter case title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the incident in detail'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'incident_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where did the incident occur?'}),
            'policy_violation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Which policy was violated?'}),
            'witnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Names and contact details of witnesses'}),
            'evidence_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe any evidence available'}),
            'assigned_investigator': forms.Select(attrs={'class': 'form-select'}),
            'committee_members': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'related_grievance': forms.Select(attrs={'class': 'form-select'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active users
        self.fields['assigned_investigator'].queryset = User.objects.filter(is_active=True)
        self.fields['committee_members'].queryset = User.objects.filter(is_active=True)
        self.fields['related_grievance'].queryset = Grievance.objects.all()
        self.fields['assigned_investigator'].required = False
        self.fields['committee_members'].required = False
        self.fields['related_grievance'].required = False

    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now().date():
            raise ValidationError("Incident date cannot be in the future.")
        return incident_date


class DisciplinaryActionForm(forms.ModelForm):
    """Form for creating/editing disciplinary actions"""
    
    class Meta:
        model = DisciplinaryAction
        fields = [
            'action_type', 'description', 'justification', 'effective_date',
            'duration_days', 'status'
        ]
        widgets = {
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the action to be taken'}),
            'justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide justification for this action'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Number of days (for suspensions, etc.)'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active action types
        self.fields['action_type'].queryset = DisciplinaryActionType.objects.filter(is_active=True)

    def clean_effective_date(self):
        effective_date = self.cleaned_data.get('effective_date')
        if effective_date and effective_date < timezone.now().date():
            raise ValidationError("Effective date cannot be in the past.")
        return effective_date

    def clean_duration_days(self):
        duration_days = self.cleaned_data.get('duration_days')
        if duration_days and duration_days <= 0:
            raise ValidationError("Duration must be greater than 0.")
        return duration_days


class DisciplinaryActionDocumentForm(forms.ModelForm):
    """Form for uploading disciplinary action documents"""
    
    class Meta:
        model = DisciplinaryActionDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of the document'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be less than 10MB.")
            
            # Check file type
            allowed_types = ['pdf', 'doc', 'docx']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_types:
                raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
        
        return file


class AppealForm(forms.ModelForm):
    """Form for filing appeals"""
    
    class Meta:
        model = Appeal
        fields = ['grounds_for_appeal', 'supporting_evidence', 'requested_outcome']
        widgets = {
            'grounds_for_appeal': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Explain the grounds for your appeal'}),
            'supporting_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide any supporting evidence or documentation'}),
            'requested_outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What outcome are you seeking?'}),
        }


class AppealReviewForm(forms.ModelForm):
    """Form for reviewing appeals"""
    
    class Meta:
        model = Appeal
        fields = ['status', 'review_notes', 'outcome']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter review notes'}),
            'outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter the outcome of the appeal'}),
        }


class EscalationMatrixForm(forms.ModelForm):
    """Form for managing escalation matrix"""
    
    class Meta:
        model = EscalationMatrix
        fields = ['level', 'department', 'role', 'user', 'is_active']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department (optional)'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active users
        self.fields['user'].queryset = User.objects.filter(is_active=True)


class GrievanceSearchForm(forms.Form):
    """Form for searching grievances"""
    STATUS_CHOICES = [('', 'All Statuses')] + Grievance.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + Grievance.PRIORITY_CHOICES
    
    ticket_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ticket Number'})
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'})
    )
    employee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from employees.models import Employee
        self.fields['employee'].queryset = Employee.objects.all()
        self.fields['category'].queryset = GrievanceCategory.objects.filter(is_active=True)


class DisciplinaryCaseSearchForm(forms.Form):
    """Form for searching disciplinary cases"""
    STATUS_CHOICES = [('', 'All Statuses')] + DisciplinaryCase.STATUS_CHOICES
    SEVERITY_CHOICES = [('', 'All Severities')] + DisciplinaryCase.SEVERITY_CHOICES
    
    case_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Case Number'})
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'})
    )
    employee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    severity = forms.ChoiceField(
        choices=SEVERITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_investigator = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from employees.models import Employee
        self.fields['employee'].queryset = Employee.objects.all()
        self.fields['assigned_investigator'].queryset = User.objects.filter(is_active=True)


class GrievanceStatusUpdateForm(forms.ModelForm):
    """Form for updating grievance status"""
    
    class Meta:
        model = Grievance
        fields = ['status', 'assigned_to', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter resolution notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False


class DisciplinaryCaseStatusUpdateForm(forms.ModelForm):
    """Form for updating disciplinary case status"""
    
    class Meta:
        model = DisciplinaryCase
        fields = ['status', 'assigned_investigator', 'hearing_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_investigator': forms.Select(attrs={'class': 'form-select'}),
            'hearing_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_investigator'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_investigator'].required = False
        self.fields['hearing_date'].required = False 