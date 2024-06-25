import re
import pandas as pd
from sqlalchemy import text
import streamlit as st
import matplotlib.pyplot as plt
from agency import Agency
from database_connection import run_query_new
import uuid

agency = Agency()

def extract_sql(response_text):
    '''Extracts SQL Query from LLM Response'''
    
   # Define a pattern that matches SQL queries enclosed in ```sql ``` format.
    pattern = r"```sql\s(.*?)```"

    # Search for the pattern using DOTALL flag to match across multiple lines
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract the SQL query without the enclosing triple backticks and 'sql'
        sql_query = match.group(1).strip()
        return sql_query
    else:
        return None

def extract_python_code(response_text):
    '''Extracts Python Code from LLM Response'''

    # Define a pattern that matches Python code enclosed in ```python ``` format.
    pattern = r"```python\s(.*?)```"

    # Search for the pattern using DOTALL flag to match across multiple lines
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract the Python code without the enclosing triple backticks and 'python'
        python_code = match.group(1).strip()
        return python_code
    else:
        return None

def get_data(message: str) -> None:
    '''Function to fetch data from SQL Query and store it in session state for further processing.'''
    decomposition = agency.user_proxy.initiate_chat(
        recipient=agency.decomposer_for_queries,
        message=message,
        max_turns=1,
    )
    query = agency.user_proxy.initiate_chat(
        recipient=agency.query_builder,
        message=decomposition.summary,
        max_turns=1,
    )
    sql_query = extract_sql(query.summary)
    st.session_state['query'] = sql_query
    if sql_query:
        query_result = run_query_new(sql_query)
        if query_result is not None:
            st.session_state['dataframes'].append(query_result)
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': query_result})
            st.session_state['fetched'] = True
        else:
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': "No data found from SQL query."})

def write_python(script_instructions: str) -> str:
    resulting_python = extract_python_code(agency.user_proxy
                                           .initiate_chat(
                                               recipient=agency.script_builder,
                                               message=script_instructions,
                                               max_turns=1).summary)
    return str(resulting_python)

def generate_unique_id():
    """
    Generate a unique identifier using UUID4.

    Returns:
        str: A unique identifier string.
    """
    return str(uuid.uuid4())

def initiate_state():
    """Initialize the session state dictionary with necessary key-value pairs."""
    if 'dataframes' not in st.session_state:
        st.session_state['dataframes'] = [pd.DataFrame(), ]
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
    if 'fetched' not in st.session_state:
        st.session_state['fetched'] = False
    if 'python_assignment' not in st.session_state:
        st.session_state['python_assignment'] = None
    if 'prompt' not in st.session_state:
        st.session_state['prompt'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'query' not in st.session_state:
        st.session_state['query'] = None
    if 'chat_id' not in st.session_state:
        st.session_state['chat_id'] = None
    if 'chat_title' not in st.session_state:
        st.session_state['chat_title'] = None
        
    