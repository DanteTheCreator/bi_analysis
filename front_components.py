import streamlit as st
from database_connection import add_temp_table, insert_into_clickhouse
from matplotlib.figure import Figure
from utils import get_data
import pandas as pd


def render_chat():
    for message in st.session_state['messages']:
        avatar_dir = './svg/ai.svg' if message['role'] == 'assistant' else './svg/user.svg'
        if isinstance(message['content'], Figure):
            st.chat_message(message['role'], avatar=avatar_dir).pyplot(
                message['content'])
        else:
            st.chat_message(message['role'], avatar=avatar_dir).write(
                message['content'])


def upload_form():
    uploaded_file = st.file_uploader("Upload a file", type=["csv"])
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            if uploaded_file.name.endswith(".csv"):
                st.session_state['uploaded_file'] = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                st.session_state['uploaded_file'] = pd.read_excel(
                    uploaded_file)
            add_temp_table(st.session_state['uploaded_file'])

        except Exception as e:
            st.error(f"Error: {str(e)}")


def reset_button():
    if st.button('Reset',type='secondary', use_container_width=True):
        st.session_state['dataframes'] = [pd.DataFrame(), ]
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
        st.session_state['fetched'] = False
        st.session_state['python_assignment'] = None
        st.session_state['chat_id'] == None
        st.session_state['uploaded_file'] = None
        st.rerun()


def fetch_button():
    if st.button('Fetch',type='primary', use_container_width=True):
        st.session_state['prompt'] = st.session_state['messages'][-2]['content']
        if 'uploaded_file' in st.session_state and not st.session_state['uploaded_file'].empty and st.session_state['uploaded_file'] is not None:
            get_data(
                f"""Use 'filter' in the db, which was created according to:
                {st.session_state['uploaded_file'].head()}
                and handle the following task:
                {''.join([str(message['content']) for message in st.session_state['messages']])}"""
            )
        else:
            get_data(
                ''.join([str(message['content']) for message in st.session_state['messages']]))
        st.session_state['fetched'] = True
        st.rerun()


def save_button():
    if st.button('Save',type='secondary', use_container_width=True):
        if st.session_state['fetched'] == True:
            try:
                insert_into_clickhouse(st.session_state['username'], st.session_state['prompt'],
                                    st.session_state['prompt'][:16], st.session_state['query'])
            except Exception as e:
                print(f'Error:  {e}')
        st.rerun()
