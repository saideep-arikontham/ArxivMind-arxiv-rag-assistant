import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.db.database import init_db, AsyncSessionLocal
from src.schemas.database.chat_schema import ChatModel, ResponseModel
from src.services.ollama.client import OllamaModel
from src.services.nvidia_nim.client import NvidiaNimModel
from src.db.utils.chat_history import insert_into_chat_history

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations/DDL once
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@app.get("/")
def root():
    return {"message": "A simple chatbot"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.post("/chat_ollama", response_model=ResponseModel)
async def chat_with_ollama(chat: ChatModel):
    try:
        model = OllamaModel()
        response = await model.prompt_model(chat.query)
        return ResponseModel(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_nvidia", response_model=ResponseModel)
async def chat_with_nvidia(
    chat: ChatModel,
    model_name: str | None = Query(None, description="Model, e.g., deepseek-ai/deepseek-v3"),
    session_id: str | None = Query(None, description="Optional session id to retain history"),
    db: AsyncSession = Depends(get_session),
):
    """
    NVIDIA NIM chat endpoint.
    - Respects `model_name` or falls back to NVIDIA_NIM_DEFAULT_MODEL
    - Partitions history by model to avoid cross-model persona bleed
    - Persists the response to Postgres (first_table)
    """
    try:
        selected_model = model_name or os.getenv(
            "NVIDIA_NIM_DEFAULT_MODEL", "moonshotai/kimi-k2-instruct-0905"
        )
        sid = session_id or f"default::{selected_model}"

        model = NvidiaNimModel(model_name=selected_model)
        user_query_timestamp = datetime.utcnow()
        response = await model.prompt_model(chat.query, session_id=sid)
        model_response_timestamp = datetime.utcnow()

        # Persist response text (adjust to your real schema later)
        await insert_into_chat_history(user_query=chat.query, 
                                       model_response=response, 
                                       model_used=selected_model,
                                       user_query_timestamp=user_query_timestamp,
                                       model_response_timestamp=model_response_timestamp,
                                       session=db)

        return ResponseModel(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
