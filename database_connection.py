
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
    ''' This function executes a SQL query against the Clickhouse database, 
    fetches the results into a pandas DataFrame, and returns it. 
    It uses the provided SQLAlchemy connection object (clickhouse_engine) 
    to connect to the Clickhouse database and execute the query. 
    If an exception occurs during execution, it prints the error message but does not stop the program.'''
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
    '''This function is similar to run_query_new() but doesn't fetch the results into a pandas DataFrame.
    It only executes the SQL query against the Clickhouse database and handles any exceptions that may occur during execution.'''
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
    '''This function adds a temporary table to the Clickhouse database called 'filter'.
    The DataFrame (df) is converted to a SQL table schema using the create_sql_table_schema() function, which is not provided in your code.
    The DataFrame is then inserted into the 'filter' table using SQLAlchemy ORM.'''
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
    '''This function inserts a new row into the 'shortcuts' table in the Clickhouse database with the provided uid, prompt, title, and query values.
    It uses SQLAlchemy ORM to create a session object, define the insertion data, and execute the SQL INSERT statement.'''
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
    ''' This function loads all shortcut data from the 'shortcuts' table in the Clickhouse database and returns it as a list of tuples.
    It uses SQLAlchemy ORM to create a session object, execute an SQL SELECT query on the 'shortcuts' table, fetch all results, and return them.'''
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
    '''This function runs a shortcut by executing its corresponding SQL query using the run_query_new() function and updating the app state with the result of the query.
    The result is stored in st.session_state['messages'], which contains a list of dictionaries representing the chat messages.
    It also updates the 'dataframes' list in st.session_state if the result is a pandas DataFrame.'''
    data = run_query_new(query)

    st.session_state['dataframes'][0] = data
    st.session_state['messages'].append({'role': 'assistant', 'content': data})
    st.session_state['fetched'] = True
    st.session_state['python_assignment'] = None


def save_chat_message(chat_id, content, author, timestamp=None):
    '''This function saves a new message to the 'chat_messages' table in the Clickhouse database with the provided chat_id, user_id, message_content, and timestamp.
    If no timestamp is provided, it defaults to the current UTC timestamp using datetime.datetime.utcnow().
    It uses parameterized queries to avoid SQL injection attacks. The function executes an SQL INSERT statement using SQLAlchemy ORM.'''
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
    '''This function saves a new chat title to the 'chat_titles' table in the Clickhouse database with the provided chat_id and title values. 
    If the chat_id already exists in the table, it updates the existing record with the new title using an ON DUPLICATE KEY UPDATE clause. 
    The function uses parameterized queries to avoid SQL injection attacks and executes an SQL INSERT statement or an UPDATE statement using SQLAlchemy ORM.'''
    
    query = text("""
    INSERT INTO chat_titles (id, title)
    VALUES (:chat_id, :title)
    ON DUPLICATE KEY UPDATE
    column1 = VALUES(column1)
    column2 = VALUES(column2);
    """)

    # Execute the SQL statement
    with clickhouse_engine.connect() as conn:
        conn.execute(query, {
            'chat_id': chat_id,
            'title': title
        })


def load_from_chat_titles():
    '''This function loads all chat titles from the 'chat_titles' table in the Clickhouse database and returns them as a list of tuples.
    It uses parameterized queries to avoid SQL injection attacks, executes an SQL SELECT query on the 'chat_titles' table, fetches all results, and returns them.'''
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


def load_saved_chat(session_id):
    ''' This function loads all messages from the 'chat_messages' table in the Clickhouse database for a specific session_id and updates the app state with these messages. 
    It also fetches dataframes if any of the messages are DataFrames. The function uses parameterized queries to avoid SQL injection attacks, executes an SQL SELECT query
    on the 'chat_messages' table, fetches all results, and updates the app state with these messages. It also sets st.session_state['fetched'] to True and clears
    st.session_state['python_assignment']. The function is called whenever a user loads a previously saved chat from the 'Load Chat' button in the app interface.'''
    query = text("""
    SELECT id, user_id, message_content, timestamp FROM chat_messages
    WHERE session_id = :session_id
    ORDER BY timestamp
    """)
    st.session_state['fetched'] = True
    st.session_state['python_assignment'] = None
    st.session_state['messages'] = []
    # Execute the query and fetch results
    with clickhouse_engine.connect() as conn:
        try:
            result = conn.execute(query, {'session_id': session_id})
            messages = result.fetchall()
            print(messages)
            for message in messages:
                st.session_state['messages'].append(
                    {'role': message[1], 'content': message[2]})
                if isinstance(message[1], pd.DataFrame):
                    st.session_state['dataframes'][0] = message[2]

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
