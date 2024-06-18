from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine(
         "clickhouse://default:asdASD123@10.4.21.11:8123/default"
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
    customer_id,
    SUM(trans_val) AS total_deposit_amount,
    MAX(transaction_date) AS last_deposit_date
FROM
    default.test_transactions_master_aggregated
WHERE
    status = 'Deposit'
GROUP BY
    customer_id
ORDER BY
    total_deposit_amount DESC
LIMIT 10
    '''))