from autogen import GroupChat, GroupChatManager, UserProxyAgent, ConversableAgent
import tempfile
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
import pandas as pd
from sqlalchemy import create_engine, text
import pandas as pd

# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()
# Create a local command line code executor.
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)
# Create Executor Agent
executor_agent = UserProxyAgent(
    "executor_agent",
    llm_config=False,  # Turn off LLM for this agent.
    code_execution_config={
        "executor": executor
    },  # Use the local command line code executor.
    human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
)

mistral = {
    "config_list": [
        {
            "model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
            "base_url": "http://localhost:1234/v1",
            "api_key": "lm-studio",
        },
    ],
    "cache_seed": None,  # Disable caching.
}

user_proxy = UserProxyAgent(
    name='user_proxy',
    llm_config=False,
)

decomposer = ConversableAgent(
    name="Decomposer",
    system_message="""You are an expert in data retrieval and analysis.
Task Decomposition:
Description: As an expert, begin by breaking down the overall task into smaller, manageable components. For example, if the task is to determine the total deposits in the last three months, clearly identify the individual elements such as the specific time frame, relevant data fields (deposit amounts and dates), and necessary calculations (sum totals).
Complexity Evaluation:
Description: Evaluate the complexity of each component identified in the decomposition stage. Consider factors like the availability of data, the necessity for joining multiple data sources, and any required transformations or calculations. Rate each component on a complexity scale (low, medium, high).
Query Strategy Decision:
Description: Decide based on the complexity evaluation whether a single comprehensive query can efficiently retrieve all the required data, or if a more segmented approach with initial data retrieval followed by further analysis is advisable. Consider factors such as data volume, processing power, and the specific capabilities of the querying agents.
Agent Role Assignment with Specific Instructions:
Output Definition for Two Consequential Agents:
Simple Query Scenario: If a single query is sufficient, the first agent will be responsible for writing and executing the query. Instructions for the query are provided within triple quotes:
Instruction for Query Writer: ''' Write and execute a SQL query to retrieve all relevant data within the specified time frame. '''
Complex Query Scenario: If the task requires further data manipulation or analysis after the initial query:
First Agent's Role: Write and execute the primary data retrieval query. Instructions:
Instruction for Query Writer: ''' Write and execute the initial data retrieval query. Ensure to capture all relevant fields for further processing. '''
Second Agent's Role: Take the raw data and conduct the necessary additional analyses or manipulations. Instructions:
Instructions for Analysis Bot: [Analyze the raw data to calculate the sum total and prepare a detailed final report based on the specifications.]
Example Task: "Calculate the total deposits in the last three months."
First Agent (Query Writer): ''' Retrieve deposit amounts and dates within the last three months from the database. '''
Second Agent (Analysis Bot): [Calculate the sum total of deposits and generate a report detailing trends and insights.]""",
    llm_config=mistral,
    human_input_mode="NEVER",
)

# Define Builder Agent
builder_agent = ConversableAgent(
    name="Builder_Agent",
    system_message="""
    ### Instruction ###
    You create the initial SQL query structure based on Decomposer's explanation and this schema:
    create table if not exists public.test_transactions_master
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
        ### Output ###
        return the query in a SQL code block""",
    llm_config=mistral,
    human_input_mode="NEVER",
)

# Define Validator Agent
validator_agent = ConversableAgent(
    name="Validator_Agent",
    system_message=""" 
    ###Instruction###
            Validate the sql query according to this schema:
            create table if not exists public.test_transactions_master
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
    ### Output ###
    If the query is incorrect return TERMINATE.
    If the query is correct, output it in sql code block.
""",
    llm_config=mistral,
    human_input_mode="NEVER",
)

group_chat = GroupChat(
    agents=[decomposer, builder_agent, validator_agent],
    messages=[],
    max_round=4,
    allow_repeat_speaker=False,
    speaker_selection_method='round_robin'
)

group_chat_manager = GroupChatManager(groupchat=group_chat, llm_config=mistral)

chat_result = user_proxy.initiate_chat(group_chat_manager, summary_method='reflection_with_llm', message=input('What data do you need?  \n'))


print(chat_result.summary)
# # Create an engine instance
# engine = create_engine(
#     "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/"
# )

# # Connect to the database
# connection = engine.connect()

# try:
#     # Get user input for the data they need
#     user_input = input("Please input what kind of data you need: ")
#     # Simulating initiating a chat to construct a safe SQL query
#     chat_result = group_chat_manager.initiate_chat(
#         message=user_input, summary_method="reflection_with_llm"
#     )
#     # Placeholder: Assume last message from the chat history is the SQL query
#     safe_sql_query = (
#         chat_result  # Ensure this step reflects actual chat output handling
#     )
#     print(safe_sql_query)
#     # Using `text` to safely handle the SQL command
#     sql_command = text(safe_sql_query)

#     # Execute the query and fetch all results
#     result_proxy = connection.execute(sql_command)
#     records = result_proxy.fetchall()

#     # Convert the results into a DataFrame
#     df = pd.DataFrame(records)
#     df.columns = (
#         result_proxy.keys()
#     )  # Set DataFrame column headers to match SQL query result

#     # Convert DataFrame to HTML and save to a file
#     html_table = df.to_html()
#     with open("data_table.html", "w") as f:
#         f.write(html_table)

# except Exception as e:
#     print("An error occurred:", e)

# finally:
#     # Close the connection
#     connection.close()
#     print("Success, database connection is closed")
