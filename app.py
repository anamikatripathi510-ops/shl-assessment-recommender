import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse
from recommender import get_chat_response

app = FastAPI(
    title="SHL AI Intern Assignment",
    description="AI-powered SHL assessment recommender chatbot.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=422, detail="messages list cannot be empty.")
    try:
        return await get_chat_response(request.messages)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
