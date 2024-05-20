import streamlit as st
from auth import SimpleAuth  # Import the SimpleAuth class

# Initialize SimpleAuth (replace 'db_url' with your actual database URL)
db_url = 'postgresql://postgres:postgres@localhost:5432/postgres'  # Example for SQLite database
auth_system = SimpleAuth(db_url)

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
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not known or password incorrect")
    return False

def registration_form():
    """Display the registration form."""
    with st.form("Register"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.form_submit_button("Register"):
            try:
                auth_system.register_user(new_username, new_password)
                st.success("User registered successfully!")
            except ValueError as e:
                st.error(str(e))



if not check_password():
    st.stop()

# Main Streamlit app starts here
st.write("Here goes your normal Streamlit app...")
st.button("Click me")

# Sidebar button to trigger the registration form

