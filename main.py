import pandas as pd
from matplotlib.figure import Figure
import streamlit as st
from agency import Agency
from utils import extract_sql, extract_python_code, convert_df_to_arrow_compatible, display_sidebar_info, display_dynamic_sidebar_info
from database_connection import run_query_new, run_query_old, check_password
import plotly.express as px

if 'dataframes' not in st.session_state:
    st.session_state['dataframes'] = [pd.DataFrame(), ]
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "assistant", "content": "How can I help you?"}]

agency = Agency()
global_context = globals()


def get_data(message):
    with st.spinner('Fetching data...'):
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
            query_result = run_query_new(sql_query)
            if query_result is not None:
                st.session_state['dataframes'].append(query_result)
            else:
                st.session_state['messages'].append(
                    {'role': 'assistant', 'contonet': "No data found from SQL query."})


if check_password():
    # Creating the selectbox
    prompt = st.text_input("Initial data retrieval:")

    if st.button(label="Fetch Data"):
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"},
            {'role': 'user', 'content': prompt}]
        st.session_state['dataframes'] = [pd.DataFrame(),]

        get_data(prompt)
        print(st.session_state['dataframes'])
        st.session_state['dataframes'] = st.session_state['dataframes'][1:]
        print(st.session_state['dataframes'])
        st.session_state['messages'].append(
            {"role": "assistant", "content": st.session_state['dataframes'][0]})

    # Accept user input
    if next_prompt := st.chat_input("What is up?"):
        st.session_state.messages.append(
            {"role": 'user', "content": next_prompt})

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
        global_context = {'dfs': st.session_state['dataframes'], 'df': None}
        exec(str(resulting_python), global_context)

        df = global_context.get('df')
        if df is not None:
            if isinstance(df, pd.DataFrame):
                df = convert_df_to_arrow_compatible(df)
                st.session_state['dataframes'].append(df)
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': df})

    for message in st.session_state.messages:
        avatar_dir = './svg/ai.svg' if message['role'] == 'assistant' else './svg/user.svg'
        if isinstance(message['content'], Figure):
            st.chat_message(message['role'], avatar=avatar_dir).pyplot(
                message['content'])
        else:
            st.chat_message(message['role'], avatar=avatar_dir).write(
                message['content'])


    # Ensure sidebar with initial data is always displayed
    if st.session_state['dataframes'][0].empty == False:
        display_sidebar_info(st.session_state['dataframes'][0])
        display_dynamic_sidebar_info(st.session_state['dataframes'][0])
