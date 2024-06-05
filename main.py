import pandas as pd
from matplotlib.figure import Figure
import streamlit as st
from agency import Agency
from utils import extract_sql, extract_python_code, convert_df_to_arrow_compatible, display_sidebar_info, display_dynamic_sidebar_info
from database_connection import run_query_old, check_password
from pandas_llm import Sandbox
from streamlit_elements import elements, dashboard, mui

agency = Agency()
global_context = globals()
df = None
col1, col2 = st.columns([5, 1])


def get_data(message):
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
                {'role': 'assistant', 'contonet': "No data found from SQL query."})


if check_password():

    if 'dataframes' not in st.session_state:
        st.session_state['dataframes'] = [pd.DataFrame(), ]
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
    if 'fetched' not in st.session_state:
        st.session_state['fetched'] = False
    if 'python_assignment' not in st.session_state:
        st.session_state['pytohn_assignment'] = None

    if next_prompt := st.chat_input("What is up?"):
        st.session_state['messages'].append(
            {'role': 'user', 'content': next_prompt})
        while not st.session_state['fetched']:
            message = agency.user_proxy.initiate_chat(recipient=agency.talker, max_turns=1, message='/n'.join([
                f"role: {message['role']} /n content: {message['content']}" for message in st.session_state['messages']])).summary
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': message})
            st.rerun()

        if st.session_state['fetched']:

            script_instructions = agency.user_proxy.initiate_chat(
                recipient=agency.decomposer_for_scripts,
                message=f'''This is dataframes heads list:{[df.head() for df in st.session_state['dataframes']]}
                    Decompose this task please: \n {next_prompt}''',
                max_turns=1).summary

            resulting_python = extract_python_code(agency.user_proxy
                                                   .initiate_chat(
                                                       recipient=agency.script_builder,
                                                       message=script_instructions,
                                                       max_turns=1).summary)
            # * Run python code
            global_context = {
                'dfs': st.session_state['dataframes'], 'df': None}
            exec(str(resulting_python), global_context)

            df = global_context.get('df')
            if df['customer_id']:
                # Ensure the column is of string type
                df['customer_id'] = df['customer_id'].astype('str')

                # Remove commas from the customer_id column
                df['customer_id'] = df['customer_id'].str.replace(',', '')

            if df is not None:
                if isinstance(df, pd.DataFrame):
                    st.session_state['dataframes'].append(df)
                st.session_state['messages'].append(
                    {'role': 'assistant', 'content': df})
                st.rerun()

    with col1:
        for message in st.session_state.messages:
            avatar_dir = './svg/ai.svg' if message['role'] == 'assistant' else './svg/user.svg'
            if isinstance(message['content'], Figure):
                st.chat_message(message['role'], avatar=avatar_dir).pyplot(
                    message['content'])
            else:
                st.chat_message(message['role'], avatar=avatar_dir).write(
                    message['content'])
    with col2:
        if st.button('Reset', use_container_width=True):
            st.session_state['dataframes'] = [pd.DataFrame(), ]
            st.session_state['messages'] = [
                {"role": "assistant", "content": "How can I help you?"}]
            st.session_state['fetched'] = False
            st.session_state['pytohn_assignment'] = None
            st.rerun()
            
            
        if st.button('Fetch', use_container_width=True):
            get_data(
                ''.join([message['content'] for message in st.session_state['messages']]))
            st.session_state['dataframes'] = st.session_state['dataframes'][1:]
            st.session_state['messages'].append(
                {"role": "assistant", "content": st.session_state['dataframes'][0]})
            st.session_state['fetched'] = True
            st.rerun()

    if st.session_state['dataframes'][0].empty == False:
        display_sidebar_info(st.session_state['dataframes'][0])
        display_dynamic_sidebar_info(st.session_state['dataframes'][0])
