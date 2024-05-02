from pandas import DataFrame
from sqlalchemy import create_engine, text
import pandas as pd
import re


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
        if records:
            df = pd.DataFrame(records, columns=result_proxy.keys())  # Create DataFrame with data and headers
        else:
            df = None  # Create empty DataFrame with headers

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
        return None


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
        return None
