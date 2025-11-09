"""
Client lleuger per consultar l'IA d'AINA amb el context de WiFi UAB.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import requests

API_URL: Final = "https://api.publicai.co/v1/chat/completions"
API_KEY: Final = os.getenv(
    "AINA_API_KEY",
    "zpka_152725c2e6f64a64a9b46a60a1a90cd6_0e09639d",
)
MODEL_NAME: Final = "BSC-LT/salamandra-7b-instruct-tools-16k"
CONTEXT_FILE: Final = Path(__file__).with_name("el_teu_arxiu.txt")


class AinaError(RuntimeError):
    """Error quan la consulta a l'API falla o la resposta no és vàlida."""


def _load_context() -> str:
    try:
        return CONTEXT_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise AinaError(f"No s'ha trobat el fitxer de context: {CONTEXT_FILE}") from exc


_CONTEXT_CACHE: str | None = None


def get_context() -> str:
    global _CONTEXT_CACHE
    if _CONTEXT_CACHE is None:
        _CONTEXT_CACHE = _load_context()
    return _CONTEXT_CACHE


def build_payload(question: str) -> dict:
    context_txt = get_context()
    user_prompt = (
        "Basant-te exclusivament en el següent context respon la pregunta:\n\n"
        f"--- CONTEXT ---\n{context_txt}\n"
        f"--- PREGUNTA ---\n{question.strip()}"
    )
    return {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ets un assistent expert de la xarxa WiFi de la UAB. "
                    "Respon en català i cita dades concretes quan sigui possible."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 500,
    }


def ask_aina(question: str) -> str:
    if not question.strip():
        raise ValueError("Cal proporcionar una pregunta.")

    payload = build_payload(question)
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise AinaError(f"No s'ha pogut contactar amb l'API d'AINA: {exc}") from exc

    if response.status_code != 200:
        raise AinaError(
            f"Error en la sol·licitud a l'API ({response.status_code}): {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise AinaError("Resposta invàlida rebuda de l'API d'AINA.") from exc


if __name__ == "__main__":
    print(ask_aina("Quin és l'AP amb menys intensitat de camp?"))
