import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
 
def display_basic_info(data):
    st.header("Basic Information")
    st.write(f"Number of entries (rows): {data.shape[0]}")
    st.write(f"Number of columns: {data.shape[1]}")
    st.write("Column Names:")
    st.write(data.columns.tolist())
    st.write("Data Types:")
    st.write(data.dtypes)
    st.write(f"Memory Usage: {data.memory_usage(deep=True).sum()} bytes")
 
def display_descriptive_stats(data):
    st.header("Descriptive Statistics")
    st.write(data.describe())
 
def display_missing_values(data):
    st.header("Missing Values")
    missing_values = data.isnull().sum()
    st.write(missing_values[missing_values > 0])
 
def display_visualizations(data):
    st.header("Data Visualizations")
    
    # Identify numerical and categorical columns
    num_cols = data.select_dtypes(include=['float64', 'int64']).columns
    cat_cols = data.select_dtypes(include=['object']).columns
    
    st.subheader("Numerical Columns")
    for col in num_cols:
        st.write(f"Distribution of {col}:")
        plt.figure(figsize=(10, 4))
        sns.histplot(data[col].dropna(), kde=True, bins=30)
        st.pyplot(plt)
    
    st.subheader("Categorical Columns")
    for col in cat_cols:
        st.write(f"Distribution of {col}:")
        plt.figure(figsize=(10, 4))
        sns.countplot(y=col, data=data)
        st.pyplot(plt)
 
def generate_summary(data):
    num_rows, num_columns = data.shape
    column_names = data.columns.tolist()
    data_types = data.dtypes.to_dict()
    memory_usage = data.memory_usage(deep=True).sum()
    missing_values = data.isnull().sum()
    missing_summary = missing_values[missing_values > 0].to_dict()
 
    summary = f"""
    ### Dataset Summary
    - **Number of entries (rows):** {num_rows}
    - **Number of columns:** {num_columns}
    - **Column Names:** {', '.join(column_names)}
    - **Data Types:**
    """
    for col, dtype in data_types.items():
        summary += f"    - **{col}:** {dtype}\n"
    
    summary += f"- **Memory Usage:** {memory_usage} bytes\n"
    summary += "- **Columns with Missing Values and Counts:**\n"
    for col, count in missing_summary.items():
        summary += f"    - **{col}:** {count} missing values\n"
 
    st.markdown(summary)
 
def handle_user_queries(data):
    st.header("Ask Questions About Your Data")
    st.write("Enter a query below to analyze the data further. For example, 'Show me the correlation matrix.'")
    
    query = st.text_input("Your Query")
    
    if query:
        try:
            result = eval(query)
            st.write(result)
        except Exception as e:
            st.write(f"Error: {e}")
 
def main():
    st.title("Automated Data Analysis App")
    st.write("Upload your CSV file to get started with the analysis.")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Load the data
        data = pd.read_csv(uploaded_file)
        
        # Display basic information
        display_basic_info(data)
        
        # Generate and display descriptive statistics
        display_descriptive_stats(data)
        
        # Display the first few rows of the dataset
        st.header("First Few Rows")
        st.write(data.head())
        
        # Identify and report missing values
        display_missing_values(data)
        
        # Display data visualizations
        display_visualizations(data)
        
        # Generate a textual summary
        generate_summary(data)
        
        # Handle user queries
        handle_user_queries(data)
 
if __name__ == "__main__":
    main()