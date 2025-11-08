from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class ChatInput(BaseModel):
    message: str


app = FastAPI(title="UAB THE HACK API", version="0.1.0")

allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
    "null",  # Navegadores abriendo index.html directamente desde el disco
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(input: ChatInput):
    """
    Punto temporal: en la demo se devolverá eco; luego se conectará al LLM/datos.
    """
    return {"answer": f"He rebut: {input.message}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
