from pandas import DataFrame
import pandas as pd
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Define the base model for the ORM
Base = declarative_base()

# Database URL
DATABASE_URL = "postgresql+asyncpg://gpt_test_user:dedismtyvneliparoli123@10.0.55.239:5432/postgres"

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create asynchronous session maker
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def run_query_async(query: str):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        finally:
        # Close the connection
            session.close()
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
