import os
from fastapi import FastAPI, HTTPException, Query
from src.services.ollama.client import OllamaModel
from src.schemas.chat_schema import ChatModel, ResponseModel
from src.services.nvidia_nim.client import NvidiaNimModel

app = FastAPI()

@app.get("/")
def root():
    return {"message": "A simple chatbot"}


@app.post("/chat_ollama", response_model=ResponseModel)
async def chat_with_model(chat: ChatModel):
    try:
        model = OllamaModel()
        response = await model.prompt_model(chat.query)
        return ResponseModel(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @app.post("/chat_nvidia", response_model=ResponseModel)
# def chat_with_model(chat: ChatModel):
#     try:
#         model = NvidiaNimModel()
#         response = model.prompt_model(chat.query)
#         return ResponseModel(response=response)
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_nvidia", response_model=ResponseModel)
async def chat_with_model(
    chat: ChatModel,
    model_name: str | None = Query(
        None, description="Model name, e.g., deepseek-ai/deepseek-v3"
    ),
    session_id: str | None = Query(
        None, description="Optional session id to retain conversation history"
    ),
):
    """
    NVIDIA NIM chat endpoint.
    - Respects the requested model via the `model_name` query param
    - Partitions chat history per model by default to avoid persona leakage
    """
    try:
        selected_model = model_name or os.getenv(
            "NVIDIA_NIM_DEFAULT_MODEL", "moonshotai/kimi-k2-instruct-0905"
        )
        # Partition history by model to avoid cross-model persona bleed
        sid = session_id or f"default::{selected_model}"

        model = NvidiaNimModel(model_name=selected_model)
        response = await model.prompt_model(chat.query, session_id=sid)

        return ResponseModel(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
