from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from assistant_core import ask_gpt_with_context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour prod : restreindre au domaine React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        result = ask_gpt_with_context(request.message)
        return {"response": result}
    except Exception as e:
        return {"response": f"Erreur serveur : {str(e)}"}
