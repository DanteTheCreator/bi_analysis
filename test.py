from autogen import GroupChat, GroupChatManager, UserProxyAgent, ConversableAgent
import tempfile
from autogen import ConversableAgent, register_function
from autogen.coding import LocalCommandLineCodeExecutor
from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd
import re

def run_query(query: str) -> DataFrame:
    engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )
    print(query)
    # Connect to the database
    connection = engine.connect()

    try:
        # Placeholder: Assume last message from the chat history is the SQL query
        safe_sql_query = query  # Ensure this step reflects actual chat output handling
        print(safe_sql_query)
        # Using `text` to safely handle the SQL command
        sql_command = text(safe_sql_query)

        # Execute the query and fetch all results
        result_proxy = connection.execute(sql_command)
        records = result_proxy.fetchall()

        # Convert the results into a DataFrame
        df = pd.DataFrame(records)
        df.columns = (
            result_proxy.keys()
        )  # Set DataFrame column headers to match SQL query result

        # Convert DataFrame to HTML and save to a file
        return df

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Close the connection
        connection.close()
        print("Success, database connection is closed")

def extract_sql(response_text):
    # Define a pattern that matches SQL queries enclosed in ```sql ``` format.
    pattern = r"```sql\s(.*?)```"

    # Search for the pattern using DOTALL flag to match across multiple lines
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract the SQL query without the enclosing triple backticks and 'sql'
        sql_query = match.group(1).strip()
        return sql_query
    else:
        return "No SQL query found in the response."

def extract_python_code(response_text):
    # Define a pattern that matches Python code enclosed in ```python ``` format.
    pattern = r"```python\s(.*?)```"

    # Search for the pattern using DOTALL flag to match across multiple lines
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract the Python code without the enclosing triple backticks and 'python'
        python_code = match.group(1).strip()
        return python_code
    else:
        return "No Python code found in the response."

# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()
# Create a local command line code executor.
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    llm_config=False,
)

# Create Executor Agent
executor_proxy_agent = UserProxyAgent(
    "executor_agent",
    llm_config=False,  # Turn off LLM for this agent.
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    code_execution_config={
        "executor": executor
    },  # Use the local command line code executor.
    human_input_mode="NEVER",  # Always take human input for this agent for safety.
)

mistral = {
    "config_list": [
        {
            "model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
            "base_url": "http://localhost:1234/v1",
            "api_key": "lm-studio",
        },
    ],
    "cache_seed": None,  # Disable caching.
}

decomposer = ConversableAgent(
    name="Decomposer",
    system_message="""
    
    Given a user's description of the type of data they need,
    decompose the task into 2 part with their own detailed sub-tasks. Focus on identifying:
    
    1. Specific data retrieval queries needed to extract the right data from the database. 
    Consider the necessary tables, fields, and conditions.
    
    2. Any required post-processing steps using Python to analyze or modify the retrieved data. 
    Outline potential operations like calculations, data transformations, or visualizations needed 
    based on the user's request.
    
    Provide a clear and concise plan that separates database operations from Python post-processing tasks. This will facilitate subsequent handling by specialized agents.
    Restrain yoursalf from giving examples or writing code. Provide a plan.

    """,
    llm_config=mistral,
)

# Define Builder Agent
query_builder = ConversableAgent(
    name="query_builder",
    description="builds SQL query",
    system_message="""
    You will recieve a task and focus on **Database Operations**. There will be a detailed plan for building an SQL query.
    Given a detailed description of the required data fields, tables, and conditions extracted by the Decomposer, construct SQL queries that accurately retrieve this data from the database. Include:

        1. Selection of relevant fields.
        2. Identification of necessary tables and how they join, if applicable.
        3. Specification of conditions and filters to apply to the data.
        4. Any sorting or grouping operations that are required.

    Generate clean and efficient SQL code that is ready to be executed to fetch the needed data from this table:
    public.test_transactions_master
                    (
                        transaction_id          bigint,
                        customer_id             integer,
                        transaction_date        timestamp with time zone,
                        trans_type_id           smallint,
                        transaction_status      char(3),
                        trans_val               double precision,
                        balance                 double precision,
                        reference_object        integer,
                        reference_object_bigint bigint
                    );
    IGNORE Python post-processing part.
    Provide single clean sql query in this format ```sql ```
    """,
    llm_config=mistral,
    human_input_mode="NEVER",
)

query_builder.register_for_llm(name="run_query", description="runs queries")(
    run_query
)
executor_proxy_agent.register_for_execution(name="run_query")(run_query)

# Define Validator Agent
script_builder = ConversableAgent(
    name="script_builder",
    description="builds python script",
    system_message=""" 
    Based on the post-processing needs identified by the Decomposer, create a Python script that performs the following operations on the data retrieved from the database:

1. Data transformations such as merging, splitting, or reshaping data.
2. Calculations or aggregations necessary for analysis.
3. Generation of visualizations or summary statistics, if requested.
4. Any additional manipulations specified to prepare the data for final presentation or further analysis.

Ensure the script is modular, well-commented, and easy to integrate with the data retrieval outputs.

""",
    llm_config=mistral,
    human_input_mode="NEVER",
)

decomposition = user_proxy.initiate_chat(
    recipient=decomposer,
    message="Top 10 users who made the most transactions past month",
    max_turns=1,

    # summary_method="reflection_with_llm",
)

df = user_proxy.initiate_chat(
    recipient=query_builder,
    message=decomposition.summary,
    max_turns=3)