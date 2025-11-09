import requests

API_KEY = "zpka_152725c2e6f64a64a9b46a60a1a90cd6_0e09639d"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 1. Defineix el camí al teu fitxer .txt
file_path = Path(__file__).with_name("el_teu_arxiu.txt")

from frontend.aina import payload, headers
import requests

@app.post("/api/chat")
def chat(input: ChatInput):
    payload["messages"][-1]["content"] = (
        f"... --- PREGUNTA ---\n {input.message}"
    )
    res = requests.post("https://api.publicai.co/v1/chat/completions", headers=headers, json=payload)
    res.raise_for_status()
    return {"answer": res.json()["choices"][0]["message"]["content"]}


# 2. Llegeix el contingut del fitxer
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        context_txt = f.read()
except FileNotFoundError:
    print(f"Error: No s'ha trobat el fitxer a la ruta '{file_path}'")
    context_txt = "ERROR: EL CONTEXT NO S'HA POGUT CARREGAR"

# 3. Insereix el text al payload mitjançant un f-string
payload = {
    "model": "BSC-LT/salamandra-7b-instruct-tools-16k",
    "messages": [
        {
            "role": "system",
            "content": "Ets un assistent expert de la xarxa WiFi de la UAB. Respon a l'usuari basant-te només en el context proporcionat."
        },
        {
            "role": "user",
            # Nota la 'f' abans de les cometes i la variable {context_txt}
            "content": f"Basant-te en el següent context, respon la meva pregunta. \n\n --- CONTEXT --- \n{context_txt}\n --- PREGUNTA --- \n Quines zones tenen mala cobertura?"
        }
    ],
    "max_tokens": 500
}

response = requests.post("https://api.publicai.co/v1/chat/completions", headers=headers, json=payload)

if response.status_code == 200:
    print(response.json()["choices"][0]["message"]["content"])
else:
    print(f"Error en la sol·licitud a l'API: {response.status_code}")
    print(response.text)