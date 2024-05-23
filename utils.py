import re
from sqlalchemy import create_engine, text
from sqlalchemy import text
import pandas as pd
import clickhouse_connect

# Define the base model for the ORM

# Create an asynchronous engine
engine = create_engine(
        "postgresql://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"
    )

def run_query_new(query):
     # Configure the connection parameters
    config = {
        'host': '10.4.21.11',
        'port': '8123',  # default ClickHouse port
        'username': 'default',
        'password': 'asdASD123',
        'database': 'default'
    }

    try:
        # Establish the connection using the config
        client = clickhouse_connect.get_client(**config)
        # Execute the query and fetch results
        result = client.query(query)
        # Convert the result into a DataFrame
        df = pd.DataFrame(result.result_rows, columns=result.column_names)
        return df
    except Exception as e:
        print("An error occurred:", e)
        return None
    finally:
        # The connection will automatically close when the client object is deleted or goes out of scope
        print("Connection closed")

def run_query_old(query: str):
    
    with engine.connect() as conn:
        try:    
            result = conn.execute(text(query))
            # Fetch the results into a DataFrame
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception as e:
            print("An error occurred:", e)

        finally:
            # Close the connection
            conn.close()
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


