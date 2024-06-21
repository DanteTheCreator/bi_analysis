
from sqlalchemy import MetaData, Table, text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from auth import SimpleAuth
import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker
from datetime import datetime

clickhouse_engine = create_engine(
    "clickhouse://default:asdASD123@10.4.21.11:8123/default"
)


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
    with clickhouse_engine.connect() as conn:
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


def run_query_void(query: str):
    with clickhouse_engine.connect() as conn:
        try:
            conn.execute(text(query))
            # Fetch the results into a DataFrame
        except Exception as e:
            print("An error occurred:", e)
        finally:
            # Close the connection
            conn.close()
            print("Success, database connection is closed")

def add_temp_table(df: pd.DataFrame):
    with clickhouse_engine.connect() as conn:
        try:
            run_query_void("DROP TABLE IF EXISTS filter;")
            # run_query_void(create_sql_table_schema(df))
            df.to_sql(name='filter', con=clickhouse_engine,
                      if_exists='replace', index=False)
            print('------------------- Added DATA -----------------------------')

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()


def insert_into_clickhouse(uid, prompt, title, query):

    metadata = MetaData()
    metadata.reflect(bind=clickhouse_engine)

    # Reflect the existing table
    table = Table('shortcuts', metadata, autoload_with=clickhouse_engine)

    # Create a session
    Session = sessionmaker(bind=clickhouse_engine)
    session = Session()

    # Define the insertion data
    insert_data = {'id': uid, 'prompt': prompt,
                   'title': title, 'query': query}

    try:
        # Insert the data
        session.execute(table.insert().values(insert_data))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


def load_from_shortcuts(table_name='shortcuts'):
    # Create an engine and a metadata object
    metadata = MetaData()
    metadata.reflect(bind=clickhouse_engine)
    # Reflect the existing table
    query = '''
    SELECT * FROM shortcuts
    '''
    with clickhouse_engine.connect() as conn:
        try:
            result = conn.execute(text(query)).fetchall()
            return result
        except SQLAlchemyError as e:
            print(f"An error occurred while loading shortcuts: {e}")


def run_shortcut(query):
    data = run_query_new(query)

    st.session_state['dataframes'][0] = data
    st.session_state['messages'].append({'role':'assistant', 'content':data})
    st.session_state['fetched'] = True
    st.session_state['python_assignment'] = None

def save_chat_message(chat_id, content, author, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()

    # Convert timestamp to string format for SQL
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # SQL statement using parameterized query
    query = text("""
    INSERT INTO chat_messages (session_id, user_id, message_content, timestamp)
    VALUES (:chat_id, :author, :content, :timestamp)
    """)

    # Execute the SQL statement
    with clickhouse_engine.connect() as conn:
        conn.execute(query, {
            'chat_id': chat_id,
            'author': author,
            'content': content,
            'timestamp': timestamp_str
        })

def save_chat_title(chat_id, title):
    # SQL statement using parameterized query
    query = text("""
    INSERT INTO chat_titles (id, title)
    VALUES (:chat_id, :title)
    """)

    # Execute the SQL statement
    with clickhouse_engine.connect() as conn:
        conn.execute(query, {
            'chat_id': chat_id,
            'title': title
        })

def load_from_chat_titles():
    # SQL query to select all records from the chat_titles table
    query = text("""
    SELECT id, title FROM chat_titles
    """)

    # Execute the query and fetch results
    with clickhouse_engine.connect() as conn:
        try:
            result = conn.execute(query)
            chat_titles = result.fetchall()
            return chat_titles
        except SQLAlchemyError as e:
            print(f"An error occurred while loading data: {e}")
            return []

def create_clickhouse_table():
    # SQL query to create the table
    query = '''
    CREATE TABLE IF NOT EXISTS default.chat_messages (
        id String,
        session_id String,
        user_id String,
        message_content String,
        timestamp DateTime
    ) 
    ENGINE = MergeTree()
    ORDER BY id;
    '''
    
    # Execute the query
    with clickhouse_engine.connect() as conn:
        try:
            conn.execute(text(query))
            print("Table 'chat_messages' created successfully.")
        except SQLAlchemyError as e:
            print(f"An error occurred while creating the table: {e}")

