from agency import Agency
from utils import extract_sql, run_query_sync
import streamlit as st
import streamlit_pandas as sp

agency = Agency()

# Initialize session state variables
if 'last_response' not in st.session_state:
    st.session_state['last_response'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "assistant", "content": "How can I help you?"}]
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = None

# Function to run async operations


def get_data(message):
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
            st.session_state['last_response'] = query_result
            st.success("Data loaded successfully.")
        else:
            st.error("No data found from SQL query.")

# Display chat messages
# for msg in st.session_state['messages']:
#     st.text_area("chat", value=msg["content"], key=msg["role"] +
#                  str(st.session_state['messages'].index(msg)), disabled=True)


options = ["bar_chart", "line_chart", "scatter_chart"]

# Creating the selectbox

st.title("Get the DATA:")
selected_option = st.selectbox("Choose an option:", options)
prompt = st.text_input("Prompt Input:")

if (df := st.session_state['last_response']) is not None:
    all_widgets = sp.create_widgets(df)
    res = sp.filter_df(df, all_widgets)
    st.write(res)
    if selected_option == 'bar_chart':
        st.bar_chart(res)
    elif selected_option == 'line_chart':
        st.line_chart(res)
    else:
        st.scatter_chart(res)


def fetch():
    with st.spinner('Fetching data...'):
        get_data(prompt)
        st.rerun()

# def main():
#     st.rerun()


if st.button(label="Fetch Data"):
    fetch()
