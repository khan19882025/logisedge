from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from user.user_model import UserProfile, Role, CustomPermission

class UserForm(UserCreationForm):
    # UserProfile fields
    employee_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter employee ID'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter address'
        }),
        required=False
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    gender = forms.ChoiceField(
        choices=[
            ('', 'Select gender'),
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False
    )

    # Work Information
    department = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department'
        }),
        required=False
    )
    position = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter position'
        }),
        required=False
    )
    hire_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter salary',
            'step': '0.01'
        }),
        required=False
    )

    # System Information
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False,
        empty_label="Select role"
    )

    class Meta:
        model = User
        fields = [
            'username', 'password1', 'password2',
            'first_name', 'last_name', 'email'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to username and password fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })

        # If this is an update (instance exists), populate profile fields
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['employee_id'].initial = profile.employee_id
                self.fields['phone'].initial = profile.phone
                self.fields['address'].initial = profile.address
                self.fields['date_of_birth'].initial = profile.date_of_birth
                self.fields['gender'].initial = profile.gender
                self.fields['department'].initial = profile.department
                self.fields['position'].initial = profile.position
                self.fields['hire_date'].initial = profile.hire_date
                self.fields['salary'].initial = profile.salary
                self.fields['role'].initial = profile.role
            except UserProfile.DoesNotExist:
                pass

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if UserProfile.objects.filter(employee_id=employee_id).exclude(user=self.instance if self.instance else None).exists():
            raise forms.ValidationError("Employee ID already exists.")
        return employee_id

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create or update UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.employee_id = self.cleaned_data['employee_id']
            profile.phone = self.cleaned_data['phone']
            profile.address = self.cleaned_data['address']
            profile.date_of_birth = self.cleaned_data['date_of_birth']
            profile.gender = self.cleaned_data['gender']
            profile.department = self.cleaned_data['department']
            profile.position = self.cleaned_data['position']
            profile.hire_date = self.cleaned_data['hire_date']
            profile.salary = self.cleaned_data['salary']
            profile.role = self.cleaned_data['role']
            
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data['profile_picture']
            
            profile.save()
        return user

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter role name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter role description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class CustomPermissionForm(forms.ModelForm):
    class Meta:
        model = CustomPermission
        fields = ['name', 'codename', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter permission name'
            }),
            'codename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter code name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter permission description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_codename(self):
        codename = self.cleaned_data.get('codename')
        if codename:
            codename = codename.lower().replace(' ', '_')
        return codename 