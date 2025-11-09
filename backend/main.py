import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from frontend.aina import AinaError, ask_aina


class ChatInput(BaseModel):
    message: str


app = FastAPI(title="UAB THE HACK API", version="0.1.0")

raw_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8001,http://localhost:8001,null",
)
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
allow_all = any(origin == "*" for origin in allowed_origins)
allow_credentials = not allow_all
if allow_all:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(input: ChatInput):
    try:
        answer = ask_aina(input.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AinaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
