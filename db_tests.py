from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd

def run_query(query: str) -> DataFrame:
    engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )
    # Connect to the database
    connection = engine.connect()

    try:
        # Placeholder: Assume last message from the chat history is the SQL query
        safe_sql_query = query  # Ensure this step reflects actual chat output handling
        # Using `text` to safely handle the SQL command
        sql_command = text(safe_sql_query)

        # Execute the query and fetch all results
        result_proxy = connection.execute(sql_command)
        records = result_proxy.fetchall()

        # Convert the results into a DataFrame
        df = pd.DataFrame(records)
        
        if records:
            df = pd.DataFrame(records)
            df.columns = result_proxy.keys()  # Assign column names if records exist
        else:
            df = pd.DataFrame(columns=result_proxy.keys())# Set DataFrame column headers to match SQL query result

        # Convert DataFrame to HTML and save to a file
        return df

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Close the connection
        connection.close()
        print("Success, database connection is closed")


df = run_query('''
SELECT
    t.customer_id,
    COUNT(t.transaction_id) AS transaction_count
FROM
    public.test_transactions_master_aggregated t
GROUP BY
    t.customer_id
ORDER BY
    transaction_count DESC
LIMIT 10;
''')
print(df)

# mistral = {
#     "config_list": [
#         {
#             "model": "gpt-3.5-turbo",
#             "base_url": "https://api.openai.com/v1/",
#             "api_key": "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",
#         },
        
#     ],
#     "cache_seed": None,  # Disable caching.
#     "temperature": 0.1
# }

# # Create Executor Agent
# executor_proxy_agent = UserProxyAgent(
#     "executor_agent",
#     llm_config=False,  # Turn off LLM for this agent.
#     is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
#     code_execution_config={
#         "executor": executor
#     },  # Use the local command line code executor.
#     human_input_mode="NEVER",  # Always take human input for this agent for safety.
#     max_consecutive_auto_reply= 2
# )


# script_builder = ConversableAgent(
#     name="script_builder",
#     description="builds python script",
#     system_message=""" 
#     Based on the post-processing needs identified by the Decomposer, create a Python script that performs the following operations on the data retrieved from the database:
        
#         1. Data transformations such as merging, splitting, or reshaping data.
#         2. Calculations or aggregations necessary for analysis.
#         3. Generation of visualizations or summary statistics, if requested.
#         4. Any additional manipulations specified to prepare the data for final presentation or further analysis.
    
#     Note: Data will already be a pandas DataFrame, avoid creating sample data in the script. 

#     Ensure the script is modular, well-commented, and easy to integrate with the data retrieval outputs.
#     Examples:
#     Shot 1:
#     Decomposition -> DataFrame Description:
#         Columns:
#         customer_id: integer
#         total_transaction_value: double precision
#         avg_transaction_value: double precision
#         Python Script:
#         Sort the DataFrame by the 'total_transaction_value' column in descending order.
#         Select the top 10 customers.
#         Create a bar chart using matplotlib with 'customer_id' on the x-axis and 'total_transaction_value' on the y-axis.
#         Set appropriate labels and title for the chart.
#     Expected python code:
#         import matplotlib.pyplot as plt df = df.sort_values('total_transaction_value', ascending=False) top_10_customers = df.head(10)  plt.figure(figsize=(12, 6)) plt.bar(top_10_customers['customer_id'], top_10_customers['total_transaction_value']) plt.xlabel('Customer ID') plt.ylabel('Total Transaction Value') plt.title('Top 10 Customers by Total Transaction Value (Last 30 Days)') plt.xticks(rotation=45) plt.show()
#     Shot 2:
#     Decompostion -> 
#         DataFrame Description:
#         Columns:
#         customer_id: integer
#         distinct_transaction_types: bigint
#         total_transaction_value: double precision
#         Python Script:
#         Create a histogram using matplotlib to visualize the distribution of 'distinct_transaction_types'.
#         Set appropriate labels and title for the histogram.
#     Expected python Output:
#     import matplotlib.pyplot as plt plt.figure(figsize=(10, 6)) plt.hist(df['distinct_transaction_types'], bins=range(df['distinct_transaction_types'].min(), df['distinct_transaction_types'].max() + 2)) plt.xlabel('Number of Transaction Types') plt.ylabel('Number of Customers') plt.title('Distribution of Transaction Types per Customer') plt.xticks(range(df['distinct_transaction_types'].min(), df['distinct_transaction_types'].max() + 1)) plt.show()
#     Shot 3:
#     Decomposition -> 
#     DataFrame Description:
#         Columns:
#         transaction_month: timestamp
#         total_transaction_value: double precision
#         Python Script:
#         Calculate the percentage change in total transaction value from the previous month and add a new column 'pct_change' to the DataFrame.
#         Create a line chart using matplotlib with 'transaction_month' on the x-axis and 'total_transaction_value' on the y-axis.
#         Set appropriate labels and title for the chart.
#         Display the results in a formatted table, including the month, total transaction value, and percentage change.
#     Expected Python Output:
#     import matplotlib.pyplot as plt df['pct_change'] = df['total_transaction_value'].pct_change() * 100 df['pct_change'] = df['pct_change'].fillna(0).round(2)  plt.figure(figsize=(12, 6)) plt.plot(df['transaction_month'], df['total_transaction_value'], marker='o') plt.xlabel('Month') plt.ylabel('Total Transaction Value') plt.title('Monthly Transaction Value Trend for Customer 12345') plt.xticks(rotation=45) plt.grid(True)  print("Month\t\tTotal Transaction Value\tPercentage Change") for index, row in df.iterrows():     print(f"{row['transaction_month'].strftime('%Y-%m')}\t\t{row['total_transaction_value']:.2f}\t\t\t{row['pct_change']:.2f}%")
# """,
#     llm_config=mistral,
#     human_input_mode="NEVER",
# )

# chat_result = executor_proxy_agent.initiate_chat(
#     script_builder,
#     message=f'write script to visualize the data with charts {df}',
# )

