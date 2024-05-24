from agency import Agency
from utils import extract_sql, run_query_new, extract_python_code, run_query_old
import streamlit as st
from auth import SimpleAuth
import pandas as pd
from matplotlib.figure import Figure

if 'dataframes' not in st.session_state:
    st.session_state['dataframes'] = [pd.DataFrame(), ]
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "assistant", "content": "How can I help you?"}]


auth_system = SimpleAuth(
    'postgresql://postgres:postgres@10.4.21.11:5432/postgres')
agency = Agency()
global_context = globals()


def check_password():
    """Returns `True` if the user had a correct password."""

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
    return

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
            query_result = run_query_old(sql_query)
            if query_result is not None:
                st.session_state['dataframes'].append(
                    query_result
                )
                st.success("Data loaded successfully.")
            else:
                st.error("No data found from SQL query.")


if check_password():
    # Creating the selectbox
    st.title("Get the DATA:")
    prompt = st.text_input("Initial data retrieval:")

    if st.button(label="Fetch Data"):
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"},
            {'role': 'user', 'content': prompt}]
        st.session_state['dataframes'] = [pd.DataFrame()]
        get_data(prompt)
        st.session_state['dataframes'] = st.session_state['dataframes'][1:]
        st.session_state['messages'].append(
            {"role": "assistant", "content": st.session_state['dataframes'][-1]})

    # Accept user input
    if next_prompt := st.chat_input("What is up?"):
        st.session_state.messages.append(
            {"role": "user", "content": next_prompt})

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
            if type(df)==type(pd.DataFrame()):
                st.session_state['dataframes'].append(df) 
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': df})
        else:
            st.error('Dataframe not defined.')

    for message in st.session_state.messages:
        avatar_dir = './svg/ai.svg' if message['role'] == 'assistant' else './svg/user.svg'
        # if isinstance(message['content'], pd.DataFrame):
        #     st.chat_message(message['role'], avatar=avatar_dir).dataframe(
        #         message['content'])
        if isinstance(message['content'], Figure):
            st.chat_message(message['role'], avatar=avatar_dir).pyplot(
                message['content'])
        else:
            st.chat_message(message['role'], avatar=avatar_dir).write(
                message['content'])
