from autogen import UserProxyAgent, ConversableAgent
import seaborn as sns
 
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
            "temperature": 1
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
            "temperature": 1
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
            Your role is to decompose data retrieval tasks from the ClickHouse database based on user requests. Follow these steps:
1. Understand the user's request and extract key information.
2. Identify the relevant tables and fields in the ClickHouse database based on the provided schema.
3. Break down the task into specific SQL operations (e.g., SELECT, JOIN, WHERE).
4. Provide clear instructions for the Query Builder to construct the SQL query.
 
SCHEMA:
- transaction_mapping table: trans_type_id, transactions_name, status, category, sign, provider, customer_id, ngr
  - Unique values for status: 'Won', 'Bet', 'Bonus', 'Deposit', 'Withdrawals', 'Fee', 'bbet', 'wwon'
  - Unique values for category: 'Slots', 'Sports', 'Casino', 'Poker', 'P2P', etc.
  - Unique values for provider: 'Golden Race', 'EGT', 'GameArt', 'NOVA', 'NetEnt', etc.
- transactions_master table: transaction_id, customer_id, transaction_date, trans_type_id, transaction_status, trans_val, balance.
  - Unique values for transaction_status: NULL, ''
 
JOINS:
- Use `trans_type_id` to join `transaction_mapping` and `transactions_master` tables.
 
EXAMPLES OF SQL TASKS:
1. **Retrieve total deposit amount for each customer for a specific date.**
   ```sql
   SELECT tm.customer_id, SUM(tm.trans_val) AS total_deposit
   FROM transactions_master tm
   JOIN transaction_mapping tmap ON tm.trans_type_id = tmap.trans_type_id
   WHERE tmap.status = 'Deposit' AND toDate(tm.transaction_date) = '2023-05-01'
   GROUP BY tm.customer_id
   ORDER BY total_deposit DESC;
Find all transactions of a particular type for a given provider.
 
sql
Copy code
SELECT tm.transaction_id, tm.customer_id, tmap.transactions_name, tm.trans_val
FROM transactions_master tm
JOIN transaction_mapping tmap ON tm.trans_type_id = tmap.trans_type_id
WHERE tmap.provider = 'NetEnt' AND tmap.status = 'Bet';
Identify customers who were active (deposited) in the previous week but churned (not deposited) in the last week.
 
Step 1: Identify customers who deposited in the previous week.
Step 2: Identify customers who did not deposit in the last week.
Step 3: Identify churned customers.
Step 4: Get daily activity for churned customers in the previous week.
sql
Copy code
SELECT tm.customer_id, toDate(tm.transaction_date) as transaction_date, SUM(tm.trans_val) AS total_deposit
FROM transactions_master tm
JOIN transaction_mapping tmap ON tm.trans_type_id = tmap.trans_type_id
WHERE tmap.status = 'Deposit'
AND toDate(tm.transaction_date) BETWEEN toDate(dateSub(week, 2, today())) AND toDate(dateSub(week, 1, today()))
AND tm.customer_id IN (
  SELECT DISTINCT prev_week.customer_id
  FROM (
      SELECT DISTINCT tm.customer_id
      FROM transactions_master tm
      JOIN transaction_mapping tmap ON tm.trans_type_id = tmap.trans_type_id
      WHERE tmap.status = 'Deposit'
      AND toDate(tm.transaction_date) BETWEEN toDate(dateSub(week, 2, today())) AND toDate(dateSub(week, 1, today()))
  ) AS prev_week
  LEFT JOIN (
      SELECT DISTINCT tm.customer_id
      FROM transactions_master tm
      JOIN transaction_mapping tmap ON tm.trans_type_id = tmap.trans_type_id
      WHERE tmap.status = 'Deposit'
      AND toDate(tm.transaction_date) BETWEEN toDate(dateSub(week, 1, today())) AND toDate(today())
  ) AS last_week
  ON prev_week.customer_id = last_week.customer_id
  WHERE last_week.customer_id IS NULL
)
GROUP BY tm.customer_id, transaction_date
ORDER BY tm.customer_id, transaction_date;
    """,
            llm_config=self.gpt_config,
        )
 
        self.query_builder = ConversableAgent(
            name="query_builder",
            description="builds SQL query",
            human_input_mode='NEVER',
            system_message="""
           Your role is to construct SQL queries based on the decomposed tasks. Follow these steps:
1. Receive task details from the Decomposer.
2. Use the provided information to construct accurate and optimized SQL queries for the ClickHouse database.
3. Ensure queries are optimized for memory efficiency and speed.
4. Provide the final SQL query for execution.
 
SCHEMA:
- transaction_mapping table: trans_type_id, transactions_name, status, category, sign, provider, customer_id, ngr
  - Unique values for status: 'Won', 'Bet', 'Bonus', 'Deposit', 'Withdrawals', 'Fee', 'bbet', 'wwon'
  - Unique values for category: 'Slots', 'Sports', 'Casino', 'Poker', 'P2P', etc.
  - Unique values for provider: 'Golden Race', 'EGT', 'GameArt', 'NOVA', 'NetEnt', etc.
- transactions_master table: transaction_id, customer_id, transaction_date, trans_type_id, transaction_status, trans_val, balance.
 
JOINS:
- Join `transaction_mapping` and `transactions_master` tables using `trans_type_id`.
 
Use ClickHouse-Specific Date Functions:
 
Use functions like subtractMonths, subtractDays, etc., for date manipulations.
Example: WHERE tm.transaction_date BETWEEN subtractMonths(now(), 1) AND now().
Avoid ORDER BY in CTEs:
 
Do not use ORDER BY inside Common Table Expressions (CTEs), especially if the CTE contains GROUP BY.
Apply ORDER BY in the final query.
Apply LIMIT in the Final Query:
 
Do not use LIMIT inside CTEs. Instead, apply LIMIT in the final query.
Example: SELECT ... FROM ... ORDER BY ... LIMIT 10.
Use Correct Functions with Correct Number of Arguments:
 
Ensure functions are used with the correct number of arguments.
Example: subtractMonths(now(), 1) instead of minus('month', 1, now()).
 
your sql code goes sql HERE
 
in your responce you should have only ONE sql query.
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
            
            NEVER say plt.gcf() plt.gca() or plt.show() or plt.savefig() or plt.close() NEVER!
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