from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd
import clickhouse_connect


client = clickhouse_connect.get_client(host='10.4.21.11', 
                                           port='8123', 
                                           username='default', 
                                           password='asdASD123', 
                                           database='default')

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

def run_query_click(query: str) -> pd.DataFrame:
    # Create a connection to the ClickHouse server    
    try:
        # Execute the query and fetch all results
        records = client.query(query)
        # Convert the results into a DataFrame
        if records:
            df = pd.DataFrame(records)
            df.columns = [col.name for col in client.query(query).columns]
        else:
            df = pd.DataFrame(columns=[col.name for col in client.query(query).columns])

        return df

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Close the connection
        client.close()
        print("Database connection is closed")

    return pd.DataFrame()  # Return an empty DataFrame in case of exceptions
df = run_query_click('''
SELECT
    tm.customer_id,
    COUNT(tm.transaction_id) AS transaction_count
FROM
    transactions_master tm
GROUP BY
    tm.customer_id
ORDER BY
    transaction_count DESC
LIMIT 10
''')
print(df)
