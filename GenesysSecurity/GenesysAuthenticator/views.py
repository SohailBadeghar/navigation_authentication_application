from django.contrib import messages
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .custom_decorator import designation_required
from .forms import GrantPermissionForm, PrivilegeFunctionValidationForm
from .models import MasterDatabase, DatabaseAccess, MasterDatabaseSchema, DatabasePermission, DatabaseTable, \
    SchemaAccess
from .postgresql_fun_call import grant_database_privileges, grant_function_validation_privileges
from .get_schema_table_column import get_remote_schemas_tables_columns, save_to_local_database
from django.http import Http404, JsonResponse
import json
from django.urls import reverse_lazy
from .utils import *


class GrantPermissionView(View):
    template_name = 'GenesysAuthenticator/database_permission_form.html'
    form_class = GrantPermissionForm
    success_url = reverse_lazy('dashboard')

    @method_decorator(login_required)
    @method_decorator(designation_required('Senior Vice President - Projects', 'Vice President',
                                           'General Manager Projects', 'Senior Project Manager',
                                           'Program Manager', 'Team Manager', 'Manager'))
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    @method_decorator(login_required)
    @method_decorator(designation_required('Senior Vice President - Projects', 'Vice President',
                                           'General Manager Projects', 'Senior Project Manager',
                                           'Program Manager', 'Team Manager', 'Manager'))
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            user = cleaned_data['user']
            granted_by = request.user
            database_name = cleaned_data['database']
            schemas = cleaned_data['schema']
            table_alias = cleaned_data['table_alias']
            func_n = 'dum_func'
            db_access = cleaned_data.get('db_access', False)
            privilege_select = cleaned_data.get('privilege_select', False)
            privilege_insert = cleaned_data.get('privilege_insert', False)
            privilege_update = cleaned_data.get('privilege_update', False)
            privilege_delete = cleaned_data.get('privilege_delete', False)
            privilege_sequence = cleaned_data.get('privilege_sequence', False)

            # Call the utility function to grant database privileges
            result = grant_database_privileges(user, schemas, table_alias, database_name, func_n, granted_by, db_access,
                                               privilege_select, privilege_insert, privilege_update, privilege_delete,
                                               privilege_sequence)

            if result and result[0][0].startswith('200'):
                # Save the form data to the DatabasePermission model
                database_permission = form.save(commit=False)
                database_permission.granted_by = granted_by
                database_permission.schemas = schemas
                database_permission.table_alias = table_alias

                # Save the instance to get an ID
                database_permission.save()

                messages.success(request, 'Database permission granted successfully.')
                return redirect(self.success_url)
            else:
                # Pass the error message to the form context
                form.add_error(None, f"Error: Database permission not created. Details: {result}")
        else:
            messages.error(request, 'Error: Form is not valid.')

        # Render the form with error messages
        return render(request, self.template_name, {'form': form})


@login_required
@designation_required('Senior Vice President - Projects', 'Vice President',
                      'General Manager Projects', 'Senior Project Manager',
                      'Program Manager', 'Team Manager', 'Manager')
def get_schema_table_col_from_server(request):
    if request.method == 'POST':

        databases_for_server1 = ["highfidelity", "poi_core", "WoNoRoadNetwork"]
        databases_for_server2 = ["highfidelity", "abcd", "db_fight"]

        for database in databases_for_server1:
            try:
                retrieve_and_save_data(database, databases_for_server1)
            except Exception as e:
                print(f"Error processing database '{database}': {e}")

        for database in databases_for_server2:
            try:
                retrieve_and_save_data(database, databases_for_server2)
            except Exception as e:
                print(f"Error processing database '{database}': {e}")

        print("Data retrieval and saving to local database complete.")

        # Redirect to the dashboard after successful data retrieval
        return redirect('dashboard')  # Replace 'dashboard' with the actual name or URL of your dashboard view

    return render(request, 'GenesysAuthenticator/trigger_data_retrieval.html')


class GrantPrivilegesFunctionValidationView(View):
    template_name = 'GenesysAuthenticator/privilege_function_validation_form.html'
    form_class = PrivilegeFunctionValidationForm
    success_url = reverse_lazy('dashboard')

    @method_decorator(login_required)
    @method_decorator(designation_required('Senior Vice President - Projects', 'Vice President',
                                           'General Manager Projects', 'Senior Project Manager',
                                           'Program Manager', 'Team Manager', 'Manager'))
    def get(self, request, *args, **kwargs):
        all_columns = set()
        for table in DatabaseTable.objects.all():
            all_columns.update(table.columns.split(','))

        form = self.form_class()
        context = {'form': form, 'all_columns': list(all_columns)}
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(designation_required('Senior Vice President - Projects', 'Vice President',
                                           'General Manager Projects', 'Senior Project Manager',
                                           'Program Manager', 'Team Manager', 'Manager'))
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            privilege_validation_instance = form.save(commit=False)
            privilege_validation_instance.granted_by = request.user

            # try:
            #     privilege_validation_instance.save()
            # except IntegrityError as e:
            #     print(f"IntegrityError: {e}")

            user = request.user
            database_id = request.POST.get('database')
            schema_id = request.POST.get('schema')
            table_id = request.POST.get('table')
            database_name = MasterDatabase.objects.get(id=database_id).database_name
            schema = MasterDatabaseSchema.objects.get(id=schema_id).schema
            table_name = DatabaseTable.objects.get(id=table_id).table_name
            column_name = request.POST.get('columns')

            result = grant_function_validation_privileges(
                user,
                schema,
                table_name,
                column_name,
                database_name,
            )

            try:
                schema_access_instance = SchemaAccess.objects.get(
                    user=user,
                    database=privilege_validation_instance.database,
                    schema=privilege_validation_instance.schema
                )
                schema_access_instance.has_access = True
                schema_access_instance.save()
            except SchemaAccess.DoesNotExist:
                SchemaAccess.objects.create(
                    user=user,
                    database=privilege_validation_instance.database,
                    schema=privilege_validation_instance.schema,
                    has_access=True
                )

            return redirect(self.success_url)
        else:
            print(form.errors)
        return render(request, self.template_name, {'form': form})


def get_schemas(request):
    database_id = request.GET.get('database_id')
    schemas = MasterDatabaseSchema.objects.filter(database_id=database_id, is_active=True).values('id', 'schema')
    return JsonResponse(list(schemas), safe=False)


def get_tables(request):
    schema_id = request.GET.get('schema_id')
    tables = DatabaseTable.objects.filter(schema_id=schema_id).values('id', 'table_name')
    return JsonResponse(list(tables), safe=False)


def get_columns(request):
    table_id = request.GET.get('table_id')
    columns = DatabaseTable.objects.get(id=table_id).columns
    return JsonResponse({'columns': json.loads(columns)})
