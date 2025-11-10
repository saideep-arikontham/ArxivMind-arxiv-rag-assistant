from pydantic import BaseModel

class ChatModel(BaseModel):
    query: str

class ResponseModel(BaseModel):
    response: str