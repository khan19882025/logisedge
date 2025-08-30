from django import forms
from django.contrib.auth.models import User
from .models import (
    LetterType, LetterTemplate, GeneratedLetter, LetterPlaceholder,
    LetterApproval, DocumentCategory, HRDocument
)
from employees.models import Employee
from django.utils import timezone


class LetterTypeForm(forms.ModelForm):
    """Form for creating and editing letter types"""
    
    class Meta:
        model = LetterType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter letter type name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LetterTemplateForm(forms.ModelForm):
    """Form for creating and editing letter templates"""
    
    class Meta:
        model = LetterTemplate
        fields = ['letter_type', 'language', 'title', 'subject', 'content', 'arabic_content', 'is_active']
        widgets = {
            'letter_type': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter template title'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter letter subject'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Enter letter content with placeholders like {{employee_name}}, {{designation}}, {{salary}}'
            }),
            'arabic_content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Enter Arabic version of the content'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LetterGenerationForm(forms.ModelForm):
    """Form for generating letters"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the employee for whom to generate the letter"
    )
    letter_type = forms.ModelChoiceField(
        queryset=LetterType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the type of letter to generate"
    )
    template = forms.ModelChoiceField(
        queryset=LetterTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the template to use"
    )
    language = forms.ChoiceField(
        choices=[('en', 'English'), ('ar', 'Arabic'), ('both', 'English & Arabic')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='en',
        help_text="Select the language for the letter"
    )
    
    class Meta:
        model = GeneratedLetter
        fields = ['employee', 'letter_type', 'template', 'subject', 'content', 'arabic_content', 
                 'issue_date', 'effective_date', 'notes', 'is_confidential']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter letter subject'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Letter content will be auto-generated from template'
            }),
            'arabic_content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Arabic content will be auto-generated from template'
            }),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make content and arabic_content readonly initially
        self.fields['content'].widget.attrs['readonly'] = True
        self.fields['arabic_content'].widget.attrs['readonly'] = True


class LetterEditForm(forms.ModelForm):
    """Form for editing generated letters"""
    
    class Meta:
        model = GeneratedLetter
        fields = ['subject', 'content', 'arabic_content', 'issue_date', 'effective_date', 'notes', 'is_confidential']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'arabic_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LetterApprovalForm(forms.ModelForm):
    """Form for letter approval"""
    
    class Meta:
        model = LetterApproval
        fields = ['status', 'comments']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter approval comments'}),
        }


class LetterSearchForm(forms.Form):
    """Form for searching letters"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by reference number, employee name, or letter type'
        })
    )
    letter_type = forms.ModelChoiceField(
        queryset=LetterType.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + GeneratedLetter.STATUS_CHOICES,
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
    created_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class DocumentCategoryForm(forms.ModelForm):
    """Form for creating and editing document categories"""
    
    class Meta:
        model = DocumentCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class HRDocumentForm(forms.ModelForm):
    """Form for uploading HR documents"""
    
    class Meta:
        model = HRDocument
        fields = ['category', 'title', 'description', 'file', 'is_active', 'is_public', 'version']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter document description'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1.0'}),
        }


class DocumentSearchForm(forms.Form):
    """Form for searching documents"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title or description'
        })
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_public = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Public'), ('False', 'Private')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    uploaded_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class LetterPlaceholderForm(forms.ModelForm):
    """Form for managing letter placeholders"""
    
    class Meta:
        model = LetterPlaceholder
        fields = ['name', 'description', 'default_value', 'is_required', 'field_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., employee_name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description of this placeholder'}),
            'default_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Default value if any'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'field_type': forms.Select(attrs={'class': 'form-select'}),
        }


class LetterPreviewForm(forms.Form):
    """Form for previewing letters before generation"""
    preview_language = forms.ChoiceField(
        choices=[('en', 'English'), ('ar', 'Arabic'), ('both', 'Both')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='en'
    )
    include_signature = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_company_logo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BulkLetterGenerationForm(forms.Form):
    """Form for generating multiple letters at once"""
    letter_type = forms.ModelChoiceField(
        queryset=LetterType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    template = forms.ModelChoiceField(
        queryset=LetterTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(status='active'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
        help_text="Select multiple employees (hold Ctrl/Cmd to select multiple)"
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now().date()
    )
    language = forms.ChoiceField(
        choices=[('en', 'English'), ('ar', 'Arabic'), ('both', 'English & Arabic')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='en'
    ) 