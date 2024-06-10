import clickhouse_connect
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from auth import SimpleAuth
import pandas as pd
import streamlit as st
import uuid
from datetime import datetime

client = clickhouse_connect.get_client(host='10.4.21.11',
                                       port='8123',
                                       username='default',
                                       password='asdASD123',
                                       database='default')

engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )
connection = engine.connect()


def add_chat_message(host, port, username, password, database, user_id, session_id, message_content, metadata=None):
    """
    Adds a chat message to the ClickHouse database.

    :param host: String. Hostname of the ClickHouse server.
    :param port: String. Port of the ClickHouse server.
    :param username: String. Username for database authentication.
    :param password: String. Password for database authentication.
    :param database: String. Name of the database.
    :param user_id: UUID. Identifier for the user sending the message.
    :param session_id: UUID. Identifier for the chat session.
    :param message_content: String. The content of the message.
    :param metadata: String. Optional JSON string with additional metadata.
    """

    # Prepare the query to insert a new message
    query = """
    INSERT INTO chat_messages (message_id, user_id, session_id, timestamp, message_content, metadata)
    VALUES (%(message_id)s, %(user_id)s, %(session_id)s, %(timestamp)s, %(message_content)s, %(metadata)s)
    """

    # Execute the query
    client.execute(query, {
        'message_id': str(uuid.uuid4()),
        'user_id': str(user_id),
        'session_id': str(session_id),
        'timestamp': datetime.now(),
        'message_content': message_content,
        'metadata': metadata
    })


def check_password():
    """Returns `True` if the user had a correct password."""
    auth_system = SimpleAuth(
        'postgresql://postgres:postgres@10.4.21.11:5432/postgres')

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        username = st.session_state["username"]
        password = st.session_state["password"]
        if auth_system.verify_user(username, password):
            st.session_state["auth"] = True
            # Don't store the username or password.
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["auth"] = False
            st.error("😕 User not known or password incorrect")

    # Return True if the username + password is validated.
    if st.session_state.get("auth", False):
        return True

    # Show inputs for username + password.
    login_form()
    return False


def run_query_new(query):
    try:
        # Execute the query and fetch results
        result = client.query(query)
        # Convert the result into a DataFrame
        df = pd.DataFrame(result.result_rows, columns=result.column_names)
        return df
    except Exception as e:
        print("An error occurred:", e)
        return None
    finally:
        # The connection will automatically close when the client object is deleted or goes out of scope
        print("Connection closed")

def run_query_void(query: str):
    with engine.connect() as conn:
        try:
            conn.execute(text(query))
            # Fetch the results into a DataFrame
        except Exception as e:
            print("An error occurred:", e)
        finally:
            # Close the connection
            conn.close()
            print("Success, database connection is closed")
            
def run_query_old(query: str):
    with engine.connect() as conn:
        try:
            result = conn.execute(text(query))
            # Fetch the results into a DataFrame
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception as e:
            print("An error occurred:", e)

        finally:
            # Close the connection
            conn.close()
            print("Success, database connection is closed")


def get_full_chat(session_id):
    # Establish a connection to the ClickHouse server

    # SQL query to select all messages from a specific chat session
    query = """
    SELECT message_id, user_id, timestamp, message_content, metadata
    FROM chat_messages
    WHERE session_id = %(session_id)s
    ORDER BY timestamp ASC
    """

    # Execute the query
    result = client.query(query, {'session_id': session_id})

    # Collecting results
    messages = []
    for row in result:
        messages.append({
            'message_id': row['message_id'],
            'user_id': row['user_id'],
            'timestamp': row['timestamp'],
            'message_content': row['message_content'],
            'metadata': row['metadata']
        })

    return messages

def create_sql_table_schema(df: pd.DataFrame, table_name: str = 'filter') -> str:
    dtype_mapping = {
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'object': 'TEXT',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP',
        'timedelta64[ns]': 'INTERVAL'
    }
    
    # List to hold column definitions
    columns = []
    
    for col_name, dtype in df.dtypes.items():
        # Get the SQL type or default to TEXT
        sql_dtype = dtype_mapping.get(str(dtype), 'TEXT')
        
        # Handle spaces and reserved keywords in column names
        if ' ' in col_name or not col_name.isidentifier():
            col_name = f'"{col_name}"'
        
        # Create column definition
        columns.append(f"{col_name} {sql_dtype}")
    
    # Join all column definitions
    columns_sql = ",\n  ".join(columns)
    
    # Construct the CREATE TABLE SQL statement
    create_table_sql = f"CREATE TEMP TABLE filter (\n  {columns_sql}\n);"
    
    return create_table_sql

def add_temp_table(df: pd.DataFrame):

    print('------------------- Connecting to the database -----------------------------')
    
    try:
        run_query_void("DROP TABLE IF EXISTS filter;")
        # run_query_void(create_sql_table_schema(df))
        df.to_sql(name = 'filter', con=engine, if_exists='replace', index=False)
        print('------------------- Added DATA -----------------------------')

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()
