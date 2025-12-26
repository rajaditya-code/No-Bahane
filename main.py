from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import time
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY not set")


# Configure Gemini (API key stays here)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# ----- BASIC CONFIG -----
RATE_LIMIT = 5          # max requests
RATE_WINDOW = 60        # seconds
usage = {}

# TEMP USER STORE (we will replace later)
USERS = {
    "aditya": {"premium": True},
    "guest": {"premium": False}
}

# ----- REQUEST SCHEMA -----
class ChatRequest(BaseModel):
    username: str
    message: str

# ----- RATE LIMIT FUNCTION -----
def check_rate_limit(username):
    now = time.time()
    history = usage.get(username, [])
    history = [t for t in history if now - t < RATE_WINDOW]

    if len(history) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    history.append(now)
    usage[username] = history

# ----- AI ENDPOINT -----
@app.post("/ai")
def ai_chat(req: ChatRequest):
    user = USERS.get(req.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    if not user["premium"]:
        raise HTTPException(status_code=403, detail="Premium required")

    check_rate_limit(req.username)

    response = client.models.generate_content(
        model="gemma-3n-e2b-it",
        contents=req.message
    )

    return {"reply": response.text}

