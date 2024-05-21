from agency import Agency
from utils import extract_sql, run_query_sync, extract_python_code
import streamlit as st
import streamlit_pandas as sp
from auth import SimpleAuth
import pandas as pd

auth_system = SimpleAuth(
    'postgresql://postgres:postgres@10.4.21.11:5432/postgres')
agency = Agency()
visual = False
globals = {'df': pd.DataFrame()}

# Initialize session state variables
if 'dataframe' not in st.session_state:
    st.session_state['dataframe'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "assistant", "content": "How can I help you?"}]
if 'auth' not in st.session_state:
    st.session_state['auth'] = False


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
            print(st.session_state)
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
            recipient=agency.decomposer,
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
            query_result = run_query_sync(sql_query)
            if query_result is not None:
                st.session_state['dataframe'] = query_result
                globals['df'] = query_result
                st.success("Data loaded successfully.")
            else:
                st.error("No data found from SQL query.")


if check_password():
    # Creating the selectbox
    st.title("Get the DATA:")
    if st.checkbox('Visual?'):
        visual = True
    prompt = st.text_input("Initial data retrieval:")

    if st.button(label="Fetch Data"):
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
        st.session_state['messages'].append(
            {'role': 'user', 'content': prompt})
        get_data(prompt)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if (df := st.session_state['dataframe']) is not None:
        all_widgets = sp.create_widgets(df)
        res = sp.filter_df(df, all_widgets)
        with st.chat_message('assistant'):
            st.write(res)
        if visual is True:
            st.bar_chart(res)
            st.line_chart(res)
            st.scatter_chart(res)

    # Accept user input
    if next_prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(next_prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        resulting_python = extract_python_code(agency.user_proxy.initiate_chat(
            recipient=agency.script_builder, message=next_prompt, max_turns=1).summary)
        with st.spinner('Python is running...'):
            exec(str(resulting_python), globals)
            df = eval('df')
            st.session_state['dataframe'] = df

        st.session_state.messages.append(st.write(df))
