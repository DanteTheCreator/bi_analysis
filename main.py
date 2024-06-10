import pandas as pd
from matplotlib.figure import Figure
import streamlit as st
from agency import Agency
from utils import extract_sql, extract_python_code, display_sidebar_info, display_dynamic_sidebar_info, run_code
from database_connection import run_query_old, check_password, add_temp_table
from pandas_llm import Sandbox

agency = Agency()
df = None
container = st.container()

def write_python(script_instructions: str) -> str:
    resulting_python = extract_python_code(agency.user_proxy
                                           .initiate_chat(
                                               recipient=agency.script_builder,
                                               message=script_instructions,
                                               max_turns=1).summary)
    return str(resulting_python)

def get_data(message: str) -> None:
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
    if sql_query:
        query_result = run_query_old(sql_query)
        if query_result is not None:
            st.session_state['dataframes'].append(query_result)
        else:
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': "No data found from SQL query."})

if check_password():
    if 'dataframes' not in st.session_state:
        st.session_state['dataframes'] = [pd.DataFrame(), ]
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
    if 'fetched' not in st.session_state:
        st.session_state['fetched'] = False
    if 'python_assignment' not in st.session_state:
        st.session_state['python_assignment'] = None

    if next_prompt := st.chat_input("What is up?"):
        st.session_state['messages'].append(
            {'role': 'user', 'content': next_prompt})
        if not st.session_state['fetched']:
            message = agency.user_proxy.initiate_chat(
                recipient=agency.talker,
                max_turns=1,
                message='\n'.join([
                    f"""role: {message['role']} \n content: {message['content']}""" 
                    for message in st.session_state['messages']
                ])
            ).summary
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': message})
            st.session_state['fetched'] = True

    if st.session_state['fetched']:
        script_instructions = agency.user_proxy.initiate_chat(
            recipient=agency.decomposer_for_scripts,
            message=f'''This is dataframes heads list:{[df.head() for df in st.session_state['dataframes']]}
                Decompose this task please: \n {next_prompt}''',
            max_turns=1).summary

        # * Run python code
        while True:
            resulting_python = write_python(script_instructions)
            local_context = {
                'dfs': st.session_state['dataframes'], 'df': None}
            error = run_code(resulting_python, local_context)
            if error is None:
                df = local_context.get('df')
                break
            else:
                script_instructions = f'''{resulting_python} had the following error: {error}; Please provide corrected code'''

        if isinstance(df, pd.DataFrame) and 'customer_id' in df.columns and not df['customer_id'].empty:
            # Ensure the column is of string type
            df['customer_id'] = df['customer_id'].astype('str')
            # Remove commas from the customer_id column
            df['customer_id'] = df['customer_id'].str.replace(',', '')

        if df is not None:
            if isinstance(df, pd.DataFrame):
                st.session_state['dataframes'].append(df)
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': df})

    with container:
        for message in st.session_state['messages']:
            avatar_dir = './svg/ai.svg' if message['role'] == 'assistant' else './svg/user.svg'
            if isinstance(message['content'], Figure):
                st.chat_message(message['role'], avatar=avatar_dir).pyplot(
                    message['content'])
            else:
                st.chat_message(message['role'], avatar=avatar_dir).write(
                    message['content'])

        if st.button('Reset', use_container_width=True):
            st.session_state['dataframes'] = [pd.DataFrame(), ]
            st.session_state['messages'] = [
                {"role": "assistant", "content": "How can I help you?"}]
            st.session_state['fetched'] = False
            st.session_state['python_assignment'] = None
            st.rerun()

        if st.button('Fetch', use_container_width=True):
            if 'uploaded_file' in st.session_state and not st.session_state['uploaded_file'].empty:
                get_data(
                    f"""Use 'filter' in the db, which was created according to:
                    {st.session_state['uploaded_file'].head()}
                    and handle the following task:
                    {''.join([str(message['content']) for message in st.session_state['messages']])}"""
                )
            else:
                get_data(
                    ''.join([str(message['content']) for message in st.session_state['messages']]))

        with st.form("file_uploader_form"):
            uploaded_file = st.file_uploader("Upload a file", type=["csv"])
            submitted = st.form_submit_button("Submit")
            
            if uploaded_file:
                st.session_state['uploaded_file'] = pd.read_csv(uploaded_file)
                if submitted:
                    print(st.session_state['uploaded_file'])
                    
                    add_temp_table(st.session_state['uploaded_file'])

    if not st.session_state['dataframes'][0].empty:
        display_sidebar_info(st.session_state['dataframes'][0])
        display_dynamic_sidebar_info(st.session_state['dataframes'][0])
