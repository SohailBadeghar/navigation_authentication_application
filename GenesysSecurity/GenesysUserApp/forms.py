from django import forms
from django.contrib.auth.forms import UserCreationForm
from .constants import DESIGNATION_CHOICES
from .models import UserDetails
from GenesysAuthenticator.models import *
from django.contrib.auth.forms import SetPasswordForm


class RegistrationForm(UserCreationForm):
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    selected_databases = forms.ModelMultipleChoiceField(
        queryset=MasterDatabase.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label='Select Databases'
    )

    class Meta:
        model = UserDetails
        fields = ['emp_id', 'email', 'designation', 'password1', 'password2', 'selected_databases']
        widgets = {
            'designation': forms.Select(choices=DESIGNATION_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

        # Save selected database names as a list of strings
        selected_databases = self.cleaned_data.get('selected_databases')
        if selected_databases:
            user.selected_databases.set(selected_databases)

        return user


class CustomPasswordResetForm(SetPasswordForm):
    emp_id = forms.CharField(max_length=255, required=True)  # Making emp_id compulsory

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required attribute to True for each field
        for field_name, field in self.fields.items():
            field.required = True

    def clean_emp_id(self):
        emp_id = self.cleaned_data['emp_id']
        # Add any custom validation logic for emp_id here
        return emp_id
