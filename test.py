from agency import Agency
from utils import extract_python_code, extract_sql, run_query

agency = Agency()

decomposition = agency.user_proxy.initiate_chat(
    recipient=agency.decomposer,
    message="Show me top 10 customers with the highest deposit, just display a table, no need for visualization.",
    max_turns=1,

    # summary_method="reflection_with_llm",
)

query = agency.user_proxy.initiate_chat(
    recipient=agency.query_builder,
    message=decomposition.summary,
    max_turns=1,
)

query = extract_sql(query.summary)
df = run_query(query)

script_to_run = None

if df is not None:
    final_result = agency.user_proxy.initiate_chat(
        agency.script_builder,
        max_turns=1,
        message=decomposition.summary,
    )
    
    script_to_run = extract_python_code(final_result.summary)
else:
    print('No data found')

if script_to_run is not None:
    exec(script_to_run, globals(), locals())
else:
    print('No python script, SQL was enough, please view the table: \n')
    print(df)