from fastapi import FastAPI, HTTPException, Body, HTTPException, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from agent import run_agent
# Existing agent logic

app = FastAPI(title="Agent API", description="API for an intelligent agent", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, replace "*" with specific origins if needed
    allow_methods=["POST","GET"],  # HTTP methods (GET, POST, etc.) or specifiy
    allow_headers=["*"],  # Allow all headers or specify
)


class AgentRequest(BaseModel):
    query: str
    # context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    result: str
    status: str
    execution_time: Optional[float] = None

# @app.post("/agent", response_model = AgentResponse)
@app.get("/")
def read_root():
    return {"message": "Travel Assistant Backend Working!"}

@app.post("/agent")

async def Agent(request: AgentRequest):
    print(f"Type of query: {type(request.query)}")
    try:
        start_time = time.time()
        
        # result = f"Processed: {request.query}"
        result = await run_agent(request.query)
        execution_time = time.time() - start_time
        
        return AgentResponse(
            result=result,
            status="success",
            execution_time=execution_time)

        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000 , reload = True)