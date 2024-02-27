from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
from .forms import RegistrationForm, CustomPasswordResetForm
from GenesysAuthenticator.postgresql_fun_call import create_user_condition_check_validations
from .models import MasterDatabase, UserDetails
from GenesysAuthenticator.models import *
from django.contrib.auth.views import (
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView
)
from .models import UserDetails
from .postgresql_auth_fuc_call import forget_password_func
from django.db import connection
from django.urls import reverse_lazy
from django.db.models import Q
from django.views import View
from django.contrib.auth.decorators import login_required
from GenesysAuthenticator.custom_decorator import designation_required


class LoginView(FormView):
    template_name = 'GenesysUserApp/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request=self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)
            messages.success(self.request, 'Login successful.')
            return redirect('dashboard')
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)


class LogoutView(TemplateView):
    template_name = 'GenesysUserApp/logout.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')


class RegistrationView(FormView):
    template_name = 'GenesysUserApp/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            username = form.cleaned_data['emp_id'].strip()
            password = form.cleaned_data['password2']
            selected_database_ids = self.request.POST.getlist('selected_databases', [])
            selected_databases = MasterDatabase.objects.filter(id__in=selected_database_ids)

            # Initialize a flag to check if any user creation failed
            user_creation_failed = False

            for database in selected_databases:
                success, message, result_third_proc = create_user_condition_check_validations(username, password,
                                                                                              database)
                if not success:
                    user_creation_failed = True
                    messages.error(form, message)  # Show error messages on the registration form

            if not user_creation_failed:
                # If all user creations were successful, display the success message
                messages.success(self.request, "User created successfully.")

                # Save the form and redirect to the success URL
                user = form.save()
                database_access = DatabaseAccess.objects.create(user=user)
                database_access.databases.set(selected_databases)
                return redirect(self.success_url)

        except Exception as e:
            print(f"Error during registration: {e}")
            form.add_error(None, 'An error occurred during registration. Please try again.')

        # If there's any error or user creation failed, return the form_invalid response
        return self.form_invalid(form)

    def form_invalid(self, form):
        first_error = list(form.errors.as_data().values())[0][
            0].message if form.errors else 'Form is not valid. Please correct the errors.'
        messages.error(self.request, first_error)
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'GenesysUserApp/change_password.html'
    success_url = reverse_lazy('password_change_done')


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'GenesysUserApp/password_change_done.html'


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'GenesysUserApp/dashboard.html'


class CustomPasswordResetView(BasePasswordResetView):
    template_name = 'GenesysUserApp/password_reset_form.html'
    email_template_name = 'GenesysUserApp/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'GenesysUserApp/password_reset_done.html'


class CustomPasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'GenesysUserApp/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        # Get the employee ID, new password, and confirm password from the form
        emp_id = form.cleaned_data.get('emp_id')
        new_password1 = form.cleaned_data.get('new_password1')
        new_password2 = form.cleaned_data.get('new_password2')
        try:
            # Validate if both passwords match
            if new_password1 != new_password2:
                # Handle the case where passwords do not match
                return self.form_invalid(form)

            # Check if the employee ID exists
            if not UserDetails.objects.filter(emp_id=emp_id).exists():
                form.add_error('emp_id', 'Employee ID does not exist')
                return self.form_invalid(form)

            # If passwords match and employee ID exists, proceed
            try:
                # Store the values in temporary variables and pass them to the function
                temp_emp_id = emp_id
                temp_new_password = new_password1
                forget_password_func(temp_emp_id, temp_new_password)
            except Exception as e:
                print(e)
                # Handle any errors that occur during the function call

        except Exception as e:
            print(e)
            # Handle any other unexpected errors

        # Continue with the default behavior of saving the form data
        return super().form_valid(form)

    def form_invalid(self, form):
        # Render the form again with errors
        return self.render_to_response(self.get_context_data(form=form))


class CustomPasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'GenesysUserApp/password_reset_complete.html'


@method_decorator(login_required, name='dispatch')
@method_decorator(designation_required('Senior Vice President - Projects', 'Vice President',
                                       'General Manager Projects', 'Senior Project Manager',
                                       'Program Manager', 'Team Manager', 'Manager'), name='dispatch')
class UserListView(View):
    def get(self, request):
        users_list = UserDetails.objects.all()

        # Search functionality
        query = request.GET.get('q')
        if query:
            users_list = users_list.filter(
                Q(emp_id__icontains=query) |  # Use Q object for OR condition
                Q(email__icontains=query) |
                Q(designation__icontains=query)
            )

        paginator = Paginator(users_list, 10)  # Show 5 users per page

        page_number = request.GET.get('page')
        users = paginator.get_page(page_number)
        total_users = users_list.count()  # Total count of users

        return render(request, 'GenesysUserApp/user_list_details.html', {'users': users, 'total_users': total_users})
