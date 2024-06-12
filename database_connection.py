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
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgre"
    )

clickhouse_engine =  create_engine(
        "clickhouse://default:asdASD123@10.4.21.11':8123/default"
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

def add_temp_table(df: pd.DataFrame):
    with engine.connect() as conn:
    
        try:
            run_query_void("DROP TABLE IF EXISTS filter;")
            # run_query_void(create_sql_table_schema(df))
            df.to_sql(name = 'filter', con=engine, if_exists='replace', index=False)
            print('------------------- Added DATA -----------------------------')

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()

def add_temp_table_clickhouse(df:pd.DataFrame):
    with clickhouse_engine.connect() as conn:
        try:
            run_query_void("DROP TABLE IF EXISTS filter;")
            # run_query_void(create_sql_table_schema(df))
            df.to_sql(name = 'filter', con=engine, if_exists='replace', index=False)
            print('------------------- Added DATA -----------------------------')

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()