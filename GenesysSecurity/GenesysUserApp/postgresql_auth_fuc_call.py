import psycopg2
from django.http import Http404
from .models import MasterDatabase


def forget_password_func(temp_emp_id, temp_new_password, database_name='highfidelity'):
    connection = None
    try:
        master_db = MasterDatabase.objects.get(database_name=database_name, is_active=True)

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

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        procedure_name = 'update_user_password'
        schema_name = 'administrative_utility'

        # Call the PostgreSQL function with parameters
        cursor.callproc(f'{schema_name}.{procedure_name}', [temp_emp_id, temp_new_password])

        # Commit the transaction
        connection.commit()

    except MasterDatabase.DoesNotExist:
        raise Http404("MasterDatabase not found with the given conditions.")

    except (Exception, psycopg2.DatabaseError) as error:
        # Rollback the transaction in case of an error
        if connection:
            connection.rollback()
        print("Error occurred:", error)

    finally:
        # Close the cursor and connection
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()
