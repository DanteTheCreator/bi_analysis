from autogen import UserProxyAgent, ConversableAgent

class Agency:
    def __init__(self,):
        self.llm_config = {
            "config_list": [
                {
                    "model": "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
                    "base_url": "http://10.80.17.130:1234/v1",
                    "api_key": "lm-studio",
                },

            ],
            "cache_seed": None,  # Disable caching.
            "temperature": 0
        }
        
        self.gpt_config = {
            "config_list": [
                {
                    "model": "gpt-4o",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "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",
                },

            ],
            "cache_seed": None,  # Disable caching.
            "temperature": 0
        }

        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            llm_config=False,
            code_execution_config=False,
            human_input_mode="NEVER",
        )

        self.decomposer_for_queries = ConversableAgent(
            name="Decomposer",
            human_input_mode='NEVER',
            system_message="""
            Have a look at the chat that will be passed to you and:
            
            Given a user's description of the data they need, decompose the task and determine how to query it from database.
            a. Provide detailed instructions for the Query Builder.
            b. Provide a description of the expected data that will be generated by the SQL query, including the column names and data types.
            
            Evaluate the decomposition to ensure it accurately captures the requirements and provides an efficient approach to retrieve and analyze the data.
            Deliver the instructions to the Query Builder.
            Avoid providing Specific data retrieval queries needed to extract the data from the database, avoid writing SQL! Provide the instructions for generating such queries (SQL)
            According to this schema:
            public.test_transactions_master_aggregated
                            (
                                column_name                 data_type
                                0           transaction_id                    bigint
                                1              customer_id                   integer
                                2         transaction_date  timestamp with time zone
                                3                trans_val          double precision
                                4                  balance          double precision
                                5         reference_object                   integer
                                6  reference_object_bigint                    bigint
                                7                   status         character varying ( status can be one of these:
                                0         bbet
                                1          Bet
                                2        Bonus
                                3      Deposit
                                4          Fee
                                5  Withdrawals
                                6          Won
                                7         wwon));
    
    """,
            llm_config=self.gpt_config,
        )

        self.query_builder = ConversableAgent(
            name="query_builder",
            description="builds SQL query",
            human_input_mode='NEVER',
            system_message="""
           You will receive a task and focus on Database Operations. There will be a detailed plan for building a PostgreSQL query. Given a detailed description of the required data fields, tables, and conditions extracted by the Decomposer, construct a SQL query that accurately retrieves this data from the database. Include:
 
Selection of relevant fields.
Identification of necessary tables and how they join, if applicable.
Specification of conditions and filters to apply to the data.
Any sorting or grouping operations that are required.
Generate clean and efficient SQL code that is ready to be executed to fetch the needed data from this table:
public.test_transactions_master_aggregated
 
column_name data_type
transaction_id  bigint
customer_id integer
transaction_date    timestamp with time zone
trans_val   double precision
balance double precision
reference_object    integer
reference_object_bigint bigint
status  character varying
Possible values for status:
 
bbet
Bet
Bonus
Deposit
Fee
Withdrawals
Won
wwon
Provide a single clean SQL query in this format:
```sql [code here]``` 

Avoid giving extra suggestions. Provide pure SQL like in the examples. 
Ensure proper error handling by avoiding the use of aliases in the WHERE 
clause or any part of the query before they are fully defined in the SELECT clause.
 
Examples:
```sql
SELECT * FROM public.test_transactions_master_aggregated;```
Explanation: This query retrieves all columns and all rows from the test_transactions_master_aggregated table. It's the simplest form of a SELECT statement and is used to display the entire content of a table.
 
```sql
SELECT transaction_id, customer_id, trans_val, balance
FROM public.test_transactions_master_aggregated
WHERE balance > 1000.0;```
Explanation: This query selects specific columns (transaction_id, customer_id, trans_val, balance) from the table, but only where the balance is greater than 1000.0. This is useful for filtering records based on specific criteria.
 
```sql
SELECT customer_id, COUNT(*) AS number_of_transactions, SUM(trans_val) AS total_spent
FROM public.test_transactions_master_aggregated
GROUP BY customer_id
HAVING SUM(trans_val) > 5000;```
Explanation: This query groups the data by customer_id and calculates two things: the total number of transactions and the total transaction value (trans_val) per customer. The HAVING clause further filters these groups to include only those customers whose total spent is greater than 5000. This is useful for summarizing data by a certain attribute.
 
```sql
SELECT transaction_id, transaction_date, trans_val
FROM public.test_transactions_master_aggregated
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY transaction_date DESC;```
Explanation: This query fetches the transaction ID, date, and value of transactions that occurred within the year 2024. The results are sorted by the transaction_date in descending order, so the most recent transactions appear first. This type of query is useful for analyzing data within a specific time frame.
 
```sql
SELECT transaction_id, trans_val, customer_id
FROM public.test_transactions_master_aggregated
WHERE customer_id IN (
    SELECT customer_id
    FROM public.test_transactions_master_aggregated
    WHERE trans_val > 1000
    GROUP BY customer_id
    HAVING COUNT(transaction_id) > 5
)
ORDER BY trans_val DESC;```
Explanation: This query selects transactions from customers who have more than five transactions exceeding a value of 1000. It uses a subquery in the WHERE clause to first identify those customer_ids meeting the criteria, and then fetches data from the main table for those customers. This is a more complex SQL operation that involves nested querying, useful for filtering data based on aggregate properties.
 
```sql
SELECT transaction_id, transaction_date, customer_id, trans_val,
    SUM(trans_val) OVER (PARTITION BY customer_id ORDER BY transaction_date) AS running_total
FROM public.test_transactions_master_aggregated
ORDER BY customer_id, transaction_date;```
Explanation: This query calculates a running total of transaction values for each customer, ordered by the transaction date. It uses a window function (SUM() OVER) which is a powerful tool for performing calculations across sets of rows that are related to the current row.
 
Final Note:
Ensure that the SQL query is clean and efficient, accurately reflecting the user’s requirements. Avoid using aliases in the WHERE clause or any conditions before they are fully defined in the SELECT clause. Handle errors by ensuring that all column references are accurate and appropriately placed.
 
 
            """,
            llm_config=self.gpt_config,
        )

        self.decomposer_for_scripts = self.script_builder = ConversableAgent(
            name="decomposer_for_scripts",
            description="decomposes tasks",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            code_execution_config=False,
            system_message="""
            Based on user's prompt:
            Decide which dataframes you need:
            Note that: Script_builder will already have full list of dataframes.
            Your job is to:
            1. figure out which dataframe script_builder MUST use from the list named 'dfs'. CHOOSE ONE: dfs[0], dfs[1], etc.YOU are the one who tells
            script_builder which dataframes to use. NEVER give ambiguous instructions.
            HOW TO choose DATAFRAME? based on user *request* and based on the *column names* in the dataframes.
            Define appropriate variables, based on the list of dataframe heads, passed in by the user.
        
            2. Decide the <final output>: pd.dataframe() or plt.figure.Figure?
            
            IF <final output> is a dataframe, write instruction for script_builder to:
            import necessary libraries
            
            Which dataframes should the script_builder modify and what kind of transformations or aggregations are needed;
            
            IF <final output> is a figure, write instruction for data scientist to:
            import the libraries
            build a complete figure
            NEVER provide actual python snippets or code, ONLY provide verbal instructions.
            INST: 1. name of the CHOSEN table (dfs[NUMBER]), 2. name of the CHOSEN column(s), 3. * aggregation(s), * transformation(s), OR visualization(s).
            your instructions go here [INST HERE]
            """)
        
        self.script_builder = ConversableAgent(
            name="script_builder",
            description="builds python script",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            code_execution_config=False,
            system_message=""" 
            You are an expert data scientist who codes in Python.
            Upon decomposers explanation which is inside [INST ], write python script to prepare and show data from the list of dataframes called 'dfs'.
            Assume that variable 'dfs' will be passed in automatically.
            Avoid creating or renaming variables.
            After imports initialize 'global dfs, df'
            which will automatically pull in that variable, after that you can use [dfs] in code.
            Decomposer will tell you which dfs you should use from the list.
            After 'global dfs, df', define the needed dataframes and apply relevant values from dfs list;
                              
            Note: avoid creating sample data in the script. Avoid leaving code half-done, avoid expecting me to fill in the code. Provide full
            code that works.
            NEVER! say plt.gcf() plt.gca() or plt.show() or plt.savefig() or plt.close() NEVER!
            ALWAYS provide python like this ```python (code here) ```;
            DO NOT assign anything to 'dfs', that list will be automatically passed in, it does not need definition from your side.
 
            IF user asks you to create a visualization such as a plot, assign completed Figure to df.
            
            General Example, how to provide
            ```python
            fig, ax = plt.subplots()
 
            # Plot data
            ax.plot(t, s, color='green')
 
            # Set the labels and title
            ax.set(xlabel='time (s)', ylabel='voltage (mV)',
                title='Example of a simple line plot')
 
            # Update label and title colors to white
            ax.title.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
 
            # Update tick colors to white
            ax.tick_params(colors='white')
            
            # Set legend with white text
            ax.legend(['line'], facecolor='none', edgecolor='white', labelcolor='white')
            
            # Set transparent background
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
            
            df = fig
            ```
            another example for dataframes:
            ```
python
import pandas as pd
 
# Initialize global dfs, df variables
global dfs, df
 
# Choose the first dataframe from the list 'dfs'
df = dfs[0]
 
# Define the transformation needed: Create a new column 'NGR' by subtracting 'total_won's from 'total_bets'
df['NGR'] = df['total_bets'] - df['total_wons']
 
df = df
```
            ALWAYS follow instructions from decomposer.
            ALWAYS understand very well whether final output should be a dataframe or a figure.
            NEVER write return df, avoid returning anything, NEVER use print, Instead you will apply it to df.
            NEVER plt.show()
            ALWAYS output ONLY ONE figure or dataframe.
            IF asked: ALWAYS construct a complete matplotlib Figure, which should have transparent background
            with green figures and white text.
            The object that would be  returned by this function, just assign it to df;
            
            for TABLES: END code with: df = df
            
            for plots and figures: END code with: df = fig
            

        """,

        )
