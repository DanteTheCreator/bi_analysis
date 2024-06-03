import clickhouse_connect
from sqlalchemy import text, create_engine
from auth import SimpleAuth
import pandas as pd
import streamlit as st
import uuid
from datetime import datetime


engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )

client = clickhouse_connect.get_client(host='10.4.21.11', 
                                           port='8123', 
                                           username='default', 
                                           password='asdASD123', 
                                           database='default')


def execute_sql_from_file(sql_file_path = './create_tables.sql'):
      # Read SQL file
    with open(sql_file_path, 'r', encoding='utf-8') as file:
        sql_commands = file.read().strip().split(';')  # Split by semicolon to get individual commands

    # Execute each command from the file
    for command in sql_commands:
        if command.strip():  # Check if command is not empty
            print(f"Executing SQL command: {command.strip()}")
            client.command(command.strip())

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
     # Configure the connection parameters
    config = {
       
    }

    try:
        # Establish the connection using the config
        client = clickhouse_connect.get_client(**config)
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
