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


# print(run_query('''ALTER TABLE default.chat_titles DELETE WHERE id = '795ec474-fcac-4c23-b217-7f2f550ab605'
#     '''))

print(run_query(''' DESCRIBE chat_messages
    '''))