from fastapi import FastAPI, HTTPException, Query
from agency import Agency
from utils import extract_sql, run_query_async


app = FastAPI()

# Initialize Agency
agency = Agency()

@app.on_event("startup")
async def startup_event():
    print("Application startup.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown.")

@app.get("/custom_report")
async def custom_report(message: str = Query(..., description="Enter your query message for the decomposer.")):
    decomposition = agency.user_proxy.initiate_chat(
        recipient=agency.decomposer,
        message=message,
        max_turns=1,
    )

    query_message = decomposition.summary
    sql_query = extract_sql(query_message)

    if not sql_query:
        raise HTTPException(status_code=400, detail="No valid SQL query extracted.")

    query_result = await run_query_async(sql_query)

    if not query_result:
        raise HTTPException(status_code=404, detail="No data found")

    return query_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
