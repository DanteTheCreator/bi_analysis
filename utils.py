import re
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import traceback
from agency import Agency
from database_connection import run_query_old, run_query_new

agency = Agency()

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

def convert_df_to_arrow_compatible(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype('str')
        elif pd.api.types.is_categorical_dtype(df[col]):
            df[col] = df[col].astype('string')
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype('bool')
        elif pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype('int64')
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype('float64')
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype('datetime64[ns]')
        elif pd.api.types.is_Int64DType(df[col]):
            df[col] = df[col].astype('str')
    return df
 
def display_sidebar_info(data):
    with st.sidebar:
        st.header("Basic Information")
        st.write(f"**Number of entries (rows):** {data.shape[0]}")
        st.write(f"**Number of columns:** {data.shape[1]}")
        st.write("**Column Names:**")
        st.write(", ".join(data.columns.tolist()))
        st.write("**Data Types:**")
        st.write(data.dtypes.to_frame().rename(columns={0: 'Type'}))
        st.write(f"**Memory Usage:** {data.memory_usage(deep=True).sum():,} bytes")
 
        st.header("Descriptive Statistics")
        st.write(data.describe())
 
        st.header("Missing Values")
        st.write(data.isnull().sum())
 
        st.header("Data Distribution")
        numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
        categorical_columns = data.select_dtypes(include=['object', 'string']).columns
 
        for col in numeric_columns:
            if 'id' in col.lower():
                continue  # Skip ID columns
            fig, ax = plt.subplots()
            sns.histplot(data[col], kde=True, color='#00FF00')
            ax.set_title(f'Distribution of {col}')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            st.pyplot(fig)
 
        for col in categorical_columns:
            fig, ax = plt.subplots()
            sns.countplot(x=data[col], color='#00FF00')
            ax.set_title(f'Distribution of {col}')
            ax.set_xlabel(col)
            ax.set_ylabel('Count')
            st.pyplot(fig)
 
        st.header("Correlation Heatmap")
        fig, ax = plt.subplots(figsize=(4, 3))
        numeric_data = data.select_dtypes(include=['float64', 'int64'])
        corr = numeric_data.corr()
        sns.heatmap(corr, ax=ax, annot=True, cmap='Greens')
        ax.set_title('Correlation Heatmap')
        st.pyplot(fig)

def display_dynamic_sidebar_info(data):
    with st.sidebar:
        st.header("Outlier Analysis")
        numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
 
        plt.style.use('dark_background')  # Applying dark theme to all plots
 
        for col in numeric_columns:
            if 'id' in col.lower():
                continue  # Skip ID columns
            fig, ax = plt.subplots()
            sns.boxplot(x=data[col], color='#00FF00')
            ax.set_title(f'Box plot of {col}')
            ax.set_xlabel(col)
            st.pyplot(fig)
 
        st.header("Trend Analysis")
        datetime_columns = data.select_dtypes(include=['datetime64[ns]']).columns
 
        for col in datetime_columns:
            fig, ax = plt.subplots()
            data.set_index(col)[numeric_columns].plot(ax=ax, color='#00FF00')
            ax.set_title(f'Time Series of {col}')
            st.pyplot(fig)
 
        st.header("Comparative Analysis")
        categorical_columns = data.select_dtypes(include=['object', 'string']).columns
        for cat_col in categorical_columns:
            for num_col in numeric_columns:
                fig, ax = plt.subplots()
                sns.violinplot(x=data[cat_col], y=data[num_col], color='#00FF00')
                ax.set_title(f'{num_col} by {cat_col}')
                ax.set_xlabel(cat_col)
                ax.set_ylabel(num_col)
                st.pyplot(fig)

def write_report(data):
    with open("data_report.txt", "w") as f:
        f.write("Data Report\n")
        f.write("="*80 + "\n\n")
        
        f.write("1. Introduction\n")
        f.write("-" * 80 + "\n")
        f.write("This report provides a comprehensive analysis of the dataset, "
                "including its structure, descriptive statistics, data distribution, "
                "missing values, and correlation between numerical features. "
                "Visualizations are included to aid in understanding the data.\n\n")
        
        f.write("2. Dataset Overview\n")
        f.write("-" * 80 + "\n")
        f.write(f"**Number of entries (rows):** {data.shape[0]}\n")
        f.write(f"**Number of columns:** {data.shape[1]}\n\n")
        f.write("**Column Names:**\n")
        f.write(", ".join(data.columns.tolist()) + "\n\n")
        f.write("**Data Types:**\n")
        f.write(data.dtypes.to_frame().rename(columns={0: 'Type'}).to_string() + "\n\n")
        f.write(f"**Memory Usage:** {data.memory_usage(deep=True).sum():,} bytes\n\n")
        
        f.write("3. Descriptive Statistics\n")
        f.write("-" * 80 + "\n")
        f.write("Descriptive statistics provide a summary of the central tendency, "
                "dispersion, and shape of the dataset’s distribution.\n\n")
        f.write(data.describe().to_string() + "\n\n")
        
        f.write("4. Missing Values\n")
        f.write("-" * 80 + "\n")
        f.write("Missing values can affect the performance of machine learning algorithms. "
                "Below is the count of missing values in each column.\n\n")
        f.write(data.isnull().sum().to_string() + "\n\n")
        
        f.write("5. Data Distribution\n")
        f.write("-" * 80 + "\n")
        f.write("This section includes the distribution of numerical and categorical variables.\n\n")
        numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
        categorical_columns = data.select_dtypes(include=['string']).columns
 
        for col in numeric_columns:
            if 'id' in col.lower():
                continue  # Skip ID columns
            f.write(f"**Distribution of {col}:**\n")
            f.write(data[col].describe().to_string() + "\n\n")
        
        for col in categorical_columns:
            f.write(f"**Distribution of {col}:**\n")
            f.write(data[col].value_counts().to_string() + "\n\n")
        
        f.write("6. Correlation Matrix\n")
        f.write("-" * 80 + "\n")
        f.write("The correlation matrix shows the relationship between numerical features. "
                "A positive value indicates a positive correlation, and a negative value indicates a negative correlation.\n\n")
        f.write(data.corr().to_string() + "\n\n")
        
        f.write("7. Detailed Column Analysis\n")
        f.write("-" * 80 + "\n")
        f.write("This section provides a detailed analysis of each column, including its distribution and key statistics.\n\n")
        
        for col in numeric_columns:
            if 'id' in col.lower():
                continue  # Skip ID columns
            f.write(f"**Analysis of {col}:**\n")
            f.write(data[col].describe().to_string() + "\n\n")
        
        for col in categorical_columns:
            f.write(f"**Analysis of {col}:**\n")
            f.write(data[col].value_counts().to_string() + "\n\n")
 
def run_code(code, global_context):
    try:
        exec(code, global_context)
    except Exception as e:
        error_message = traceback.format_exc()
        return error_message
    return None

def get_data(message: str) -> None:
    
    decomposition = agency.user_proxy.initiate_chat(
        recipient=agency.decomposer_for_queries,
        message=message,
        max_turns=1,
    )
    query = agency.user_proxy.initiate_chat(
        recipient=agency.query_builder,
        message=decomposition.summary,
        max_turns=1,
    )
    sql_query = extract_sql(query.summary)
    
    if sql_query:
        query_result = run_query_old(sql_query)
        if query_result is not None:
            st.session_state['dataframes'].append(query_result)
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': query_result})
            st.session_state['fetched'] = True
        else:
            st.session_state['messages'].append(
                {'role': 'assistant', 'content': "No data found from SQL query."})

def write_python(script_instructions: str) -> str:
    resulting_python = extract_python_code(agency.user_proxy
                                           .initiate_chat(
                                               recipient=agency.script_builder,
                                               message=script_instructions,
                                               max_turns=1).summary)
    return str(resulting_python)

def initiate_state():
    if 'dataframes' not in st.session_state:
        st.session_state['dataframes'] = [pd.DataFrame(), ]
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "assistant", "content": "How can I help you?"}]
    if 'fetched' not in st.session_state:
        st.session_state['fetched'] = False
    if 'python_assignment' not in st.session_state:
        st.session_state['python_assignment'] = None
    if 'prompt' not in st.session_state:
        st.session_state['prompt'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    