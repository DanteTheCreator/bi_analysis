import pandas as pd
import streamlit as st
from agency import Agency
from utils import write_python, initiate_state, generate_unique_id
from database_connection import check_password, load_from_shortcuts, run_shortcut, save_chat_message, save_chat_title, load_from_chat_titles, load_saved_chat
from sandbox import MinimalSandbox
from front_components import fetch_button, upload_form, reset_button, render_chat, save_button
import datetime

agency = Agency()
df = None
python_sandbox = MinimalSandbox()
initiate_state()


# * check if user is authenticated
if check_password():
    # * generate a unique id for the new chat session
    
    if st.session_state['chat_id'] == None:
        st.session_state['chat_id'] = generate_unique_id()
    
    # * Load shortcuts and past chats 
    data = load_from_shortcuts() or None
    saved_chats = load_from_chat_titles() or None
    
    # * render chat and upload form
    with st.container():
        render_chat()
        upload_form()
        
    # * render chat input
    with st.container():
        if next_prompt := st.chat_input("What is up?"):
            
            if len(st.session_state['messages']) < 2:
                message = agency.user_proxy.initiate_chat(
                    recipient=agency.talker,
                    max_turns=1,
                    message=f'Come up with a short title for the prompt: {next_prompt}'
                ).summary
                st.session_state['chat_title'] = message
                
                save_chat_title(st.session_state['chat_id'], st.session_state['chat_title'])
                
            # * append what user says to messages
            st.session_state['messages'].append(
                {'role': 'user', 'content': next_prompt})
            save_chat_message(st.session_state['chat_id'], next_prompt, 'user', datetime.datetime.now())
            
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
                save_chat_message(st.session_state['chat_id'], message, 'assistant', datetime.datetime.now())
                
                
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
                        df = python_sandbox.execute(resulting_python, global_context )
                        print(f'after Python: \n {df}')
                        break
                    
                    except Exception as e:
                        print(e)
                        st.session_state['python_assignment'] = f'''{resulting_python} had the following error: {
                            e}; Please provide corrected code'''
                st.session_state['python_assignment'] = None
            # * acive df is present
            if df is not None:
                if isinstance(df, pd.DataFrame):
                    st.session_state['dataframes'].append(df)
                    save_chat_message(st.session_state['chat_id'], df.to_json(orient='records'), 'user', datetime.datetime.now())
                st.session_state['messages'].append(
                    {'role': 'assistant', 'content': df})
                
            st.rerun()

    # * Render buttons
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        
        with col1:
            reset_button()
        with col2:
            fetch_button()
        with col3:
            save_button()
            
    # * Render shortcuts and saved chats in sidebar
    with st.sidebar:
        if data is not None:
            for row in data:
                st.button(row[2], row[1], on_click=lambda x=row[-1]: run_shortcut(x))
            st.divider()
        if saved_chats is not None:
            for row in saved_chats:
                st.button(row[1], f'KEY - {row[0]}', on_click=lambda x=row[0]: load_saved_chat(x))

    