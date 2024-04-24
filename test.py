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
executor_proxy_agent = UserProxyAgent(
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

decomposer = ConversableAgent(
    name="Decomposer",
    system_message="""You are an expert in problem solving and analytics.
Task Decomposition:
    Description: As an expert, begin by breaking down the overall task into smaller, manageable components. For example, if the task is to determine the total deposits in the last three months, clearly identify the individual elements such as the specific time frame, relevant data fields (deposit amounts and dates), and necessary calculations (sum totals).
Complexity Evaluation:
    Description: Evaluate the complexity of each component identified in the decomposition stage. Consider factors like the availability of data, the necessity for joining multiple data sources, and any required transformations or calculations. Rate each component on a complexity scale (low, medium, high).
Query Strategy Decision:
    Description: Decide based on the complexity evaluation whether a single comprehensive query can efficiently retrieve all the required data, or if a more segmented approach with initial data retrieval followed by further analysis is advisable. Consider factors such as data volume, processing power, and the specific capabilities of the querying agents.
    If the task can be accomplished with only simple SQL, return the correct query in ```query``` this format.
    If the task is too complex for SQL only, divide it into 2 parts. 
    1) How to write the SQL needed for getting the data;
    2) How to write python needed for modifyaing the data we got from the query (use pandas)
""",
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


chat_result = executor_proxy_agent.initiate_chat(
    recipient=decomposer,
    message="Top 10 users who made the most transactions past month",
    max_turns=2,
    summary_method='reflection_with_llm'
)


