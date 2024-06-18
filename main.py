import pandas as pd
import streamlit as st
from agency import Agency
from utils import write_python, display_sidebar_info, display_dynamic_sidebar_info, run_code, initiate_state
from database_connection import check_password, load_from_clickhouse, run_shortcut
from pandas_llm import Sandbox
from front_components import fetch_button, upload_form, reset_button, render_chat, save_button

agency = Agency()
df = None
initiate_state()

if check_password():
    if not st.session_state['fetched']:
        data = load_from_clickhouse()
        with st.sidebar:
            if data is not None:
                for row in data:
                    st.button(row['Title'], row['prompt'], on_click= run_shortcut(row['query']))
            else:
                st.write("You don't have shortcuts yet. Press Save Button after successful query.")
    with st.container():
        render_chat()
        upload_form()
    with st.container():

        if next_prompt := st.chat_input("What is up?"):
            # append what user says
            st.session_state['messages'].append(
                {'role': 'user', 'content': next_prompt})
            
            #* Talking with 'talker' until user presses fetch button
            if not st.session_state['fetched']:
                message = agency.user_proxy.initiate_chat(
                    recipient=agency.talker,
                    max_turns=1,
                    message='\n'.join([
                        f"""role: {message['role']}
                            \n content: {message['content']}"""
                        for message in st.session_state['messages']
                    ])
                ).summary
                st.session_state['messages'].append(
                    {'role': 'assistant', 'content': message})
                
                
            #* when we have fetched data, but user hasn't said what to do with it further (with python)
            if st.session_state['fetched'] and (st.session_state['python_assignment'] is None):
                script_instructions = agency.user_proxy.initiate_chat(
                    recipient=agency.decomposer_for_scripts,
                    message=f'''This is dataframes heads list:{[df.head() for df in st.session_state['dataframes']]}
                        Decompose this task please: \n {next_prompt}''',
                    max_turns=1).summary
                st.session_state['python_assignment'] = script_instructions
                
            #* when decomposer gives the instructions, until correct python is produced
            if st.session_state['python_assignment'] is not None:
                
                while True:
                    try:
                        resulting_python = write_python(
                            st.session_state['python_assignment'])
                        global_context = globals()
                        global_context['dfs'] = st.session_state['dataframes']
                        run_code(resulting_python, global_context )
                        df = global_context.get('df')
                        print(df)
                        break
                    
                    except Exception as e:
                        print(e)
                        st.session_state['python_assignment'] = f'''{resulting_python} had the following error: {
                            e}; Please provide corrected code'''
                st.session_state['python_assignment'] = None
            #acive df is present
            if df is not None:
                if isinstance(df, pd.DataFrame):
                    st.session_state['dataframes'].append(df)
                st.session_state['messages'].append(
                    {'role': 'assistant', 'content': df})
            st.rerun()

    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            reset_button()
        with col2:
            fetch_button()
        with col3:
            save_button()
    
        
    
    if not st.session_state['dataframes'][0].empty:
        display_sidebar_info(st.session_state['dataframes'][0])
        display_dynamic_sidebar_info(st.session_state['dataframes'][0])

