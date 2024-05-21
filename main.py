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


def fetch():
    with st.spinner('Fetching data...'):
        get_data(prompt)
        st.rerun()

# Creating the selectbox

st.title("Get the DATA:")
prompt = st.text_input("Prompt Input:")
visual = False
if st.checkbox('Visual?'):
    visual = True
if st.button(label="Fetch Data"):
    fetch()

# # Display chat messages
# for msg in st.session_state['messages']:
#     st.text_area("chat", value=msg["content"], key=msg["role"] +
#                  str(st.session_state['messages'].index(msg)), disabled=True)

if (df := st.session_state['last_response']) is not None:
    all_widgets = sp.create_widgets(df)
    res = sp.filter_df(df, all_widgets)
    st.write(res)
    if visual is True:
        st.bar_chart(res)
        st.line_chart(res)
        st.scatter_chart(res)



# def main():
#     st.rerun()

