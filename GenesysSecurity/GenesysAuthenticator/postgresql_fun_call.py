import psycopg2
from django.http import Http404
from .models import MasterDatabase


def create_user_in_database(username, password, db_server, db_port, db_username, db_password, database):
    """
    Creates a user in the specified PostgreSQL database.
    Returns a tuple containing (status, message, result_third_proc).
    """
    connection_params = {
        'host': db_server,
        'database': database.database_name,
        'user': db_username,
        'password': db_password,
        'port': db_port,
    }

    count_and_insert_initial_users = 'count_and_insert_initial_users'
    procedure_name = 'create_user_with_password'
    count_and_compare_users = 'count_and_compare_users'
    schema_name = 'administrative_utility'

    try:
        with psycopg2.connect(**connection_params) as conn, conn.cursor() as cursor:
            # Call the first stored procedure
            try:
                cursor.callproc(f'{schema_name}.{count_and_insert_initial_users}', [db_server, username])
                result_first_proc = cursor.fetchone()
                status_code = int(result_first_proc[0].split(':')[0])
                if status_code != 200:
                    return False, f"Error calling {count_and_insert_initial_users} procedure: {result_first_proc[0]}", None
            except psycopg2.Error as e:
                error_message = str(e)
                print(f"Error calling {count_and_insert_initial_users} procedure: {error_message}")
                return False, f"Error calling {count_and_insert_initial_users} procedure: {error_message}", None

            # Call the second stored procedure to create a user with a password
            try:
                cursor.callproc(f'{schema_name}.{procedure_name}', [username, password])
                result_second_proc = cursor.fetchone()
                status_code = int(result_second_proc[0].split(':')[0])
                if status_code != 200:
                    return False, f"Error calling {procedure_name} procedure: {result_second_proc[0]}", None
            except psycopg2.Error as e:
                error_message = str(e)
                print(f"Error calling {procedure_name} procedure: {error_message}")
                return False, f"Error calling {procedure_name} procedure: {error_message}", None

            # Call the third stored procedure
            try:
                cursor.callproc(f'{schema_name}.{count_and_compare_users}', [db_server, username])
                result_third_proc = cursor.fetchone()
                status_code = int(result_third_proc[0].split(':')[0])
                if status_code == 200:
                    return True, f"User created successfully: {result_third_proc[0]}", result_third_proc
                else:
                    return False, f"Error calling {count_and_compare_users} procedure: {result_third_proc[0]}", result_third_proc
            except psycopg2.Error as e:
                error_message = str(e)
                print(f"Error calling {count_and_compare_users} procedure: {error_message}")
                return False, f"Error calling {count_and_compare_users} procedure: {error_message}", None

            # Retrieve all the rows returned by the stored procedure
            result_set = cursor.fetchall()
            conn.commit()

            print(f"User created successfully in {database.database_name} on server {db_server}!")
            return True, f"User created successfully in {database.database_name} on server {db_server}!", None

    except psycopg2.Error as e:
        error_message = str(e)
        print(f"Error creating user in {database.database_name} on server {db_server}: {error_message}")
        return False, f"Error creating user in {database.database_name} on server {db_server}: {error_message}", None
    except Exception as e:
        print(f"Unexpected error creating user in {database.database_name} on server {db_server}: {e}")
        return False, f"Unexpected error: {e}", None


def create_user_condition_check_validations(username, password, database):
    """
    Checks conditions and creates a user in the specified PostgresSQL database if conditions are met.
    """
    db_server = database.server_ip
    db_port = database.port
    db_username = database.username
    db_password = database.password

    databases_for_server1 = ["highfidelity", "poi_core", "WoNoRoadNetwork"]
    databases_for_server2 = ["highfidelity", "adas", "innomap"]

    try:
        if db_server == "127.0.0.1" and database.database_name in databases_for_server1:
            success, message, result_third_proc = create_user_in_database(username, password, db_server, db_port,
                                                                          db_username, db_password, database)
            return success, message, result_third_proc

        elif db_server == "172.16.1.1" and database.database_name in databases_for_server2:
            success, message, result_third_proc = create_user_in_database(username, password, db_server, db_port,
                                                                          db_username, db_password, database)
            return success, message, result_third_proc

        return True, f"User created successfully in {database.database_name} on server {db_server}!"

    except psycopg2.Error as e:
        error_message = str(e)
        print(f"PostgresSQL Error: {e}")
        return False, f"Error creating user in {database.database_name} on server {db_server}: {error_message}"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, f"Unexpected error: {e}"


def grant_database_privileges(user, schemas, table_alias, database_name, func_n, granted_by,
                              db_access=False, privilege_select=False, privilege_insert=False,
                              privilege_update=False, privilege_delete=False, privilege_sequence=False,
                              ):
    """
       Grants database privileges to the specified user for a specific function in PostgresSQL.
    """
    try:
        try:
            master_db = MasterDatabase.objects.get(database_name=database_name, is_active=True)
        except MasterDatabase.DoesNotExist:
            raise Http404("MasterDatabase not found with the given conditions.")

        # Get the emp_id from the user
        user_emp_id = user.emp_id

        granted_by = granted_by.emp_id

        schema = schemas.schema

        # Extract relevant fields from MasterDatabase
        db_name = master_db.database_name
        username = master_db.username
        password = master_db.password
        server_ip = master_db.server_ip
        port = master_db.port

        # Establish a connection using the extracted configuration
        connection = psycopg2.connect(
            dbname=db_name,
            user=username,
            password=password,
            host=server_ip,
            port=port
        )

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Call the PostgreSQL function
        # cursor.callproc('grant_privs', [user_emp_id, db_name, func_n,
        #                                 db_access, privilege_select, privilege_insert,
        #                                 privilege_update, privilege_delete, privilege_sequence, schema_names])

        procedure_name = 'grant_privs'
        schema_name = 'administrative_utility'
        try:
            cursor.callproc(f'{schema_name}.{procedure_name}', [user_emp_id, db_name, func_n,
                                                                db_access, privilege_select, privilege_insert,
                                                                privilege_update, privilege_delete, privilege_sequence,
                                                                schema, table_alias, granted_by])
        except psycopg2.Error as e:
            error_message = str(e)
            print(f"Error calling {procedure_name} procedure: {error_message}")
            # Handle or raise the error as needed
            raise YourCustomError(error_message)

        # Retrieve all the rows returned by the stored procedure
        result_set = cursor.fetchall()

        # Commit the changes to the database
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        print("Stored procedure executed successfully")

        # Assuming the result_set contains multiple values (rows)
        return result_set



    except psycopg2.Error as e:
        error_message = str(e)
        print(f"PostgresSQL Error: {error_message}")

    except Exception as e:
        print(f"Unexpected error: {e}")


def grant_function_validation_privileges(user, schema, table_name, column_name, database_name):
    """
       Grants function validation privileges to the specified schema, table ,columns  in PostgresSQL.

    """
    try:
        try:
            master_db = MasterDatabase.objects.get(database_name=database_name, is_active=True)
        except MasterDatabase.DoesNotExist:
            raise Http404("MasterDatabase not found with the given conditions.")

        user = user.emp_id

        db_name = master_db.database_name
        username = master_db.username
        password = master_db.password
        server_ip = master_db.server_ip
        port = master_db.port

        # Establish a connection using the extracted configuration
        connection = psycopg2.connect(
            dbname=db_name,
            user=username,
            password=password,
            host=server_ip,
            port=port
        )

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Call the PostgresSQL function
        # cursor.callproc('valid_func',
        #                 [user, schema_name, table_name, column_name])

        procedure_name = 'valid_func'
        schema_name = 'administrative_utility'
        cursor.callproc(f'{schema_name}.{procedure_name}',
                        [user, schema, table_name, column_name])

        # Commit the changes to the database
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return 'validation granted successfully'
    except Exception as e:
        print(e)
        return f'Error: {e}'
