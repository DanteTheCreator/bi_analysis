from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )
    # Connect to the database
connection = engine.connect()

def run_query(query: str) -> DataFrame:
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
        # Convert DataFrame to HTML and save to a file
        return df

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Close the connection
        connection.close()
        print("Success, database connection is closed")


print(run_query('''SELECT
    t.transaction_id,
    t.customer_id,
    t.transaction_date,
    t.trans_val,
    t.balance,
    t.status
FROM
    public.test_transactions_master_aggregated AS t
INNER JOIN
    filter AS f
ON
    t.customer_id = f.customer_id
ORDER BY
    t.transaction_date DESC;'''))