from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import threading
import time
import sys
import uvicorn
import requests # Necessário para o envio HTTP

app = FastAPI()

# --- Estado global ---
myProcessId = 0
# Relógio lógico simples (inteiro) 
logical_clock = 0 

posts = {} # Dict para acesso rápido por ID
replies = defaultdict(list)

# Configuração dos pares 
processes = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082"
]

# --- Modelo de evento ---
class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    timestamp: Optional[int] = None

# --- Funções Auxiliares de Rede ---
def send_thread(url, payload):
    try:
        # Delay artificial para testar inconsistência (opcional)
        if myProcessId == 0: time.sleep(2) 
        requests.post(f"{url}/share", json=payload, timeout=5)
    except Exception as e:
        print(f"Falha ao enviar para {url}: {e}")

def async_send(payload: dict):
    # Envia para todos exceto ele mesmo
    for i, url in enumerate(processes):
        if i != myProcessId:
            t = threading.Thread(target=send_thread, args=(url, payload))
            t.start()

# --- Lógica de Aplicação ---

def processMsg(msg: Event):
    global logical_clock
    
    # Atualiza relógio lógico (Lamport) na recepção
    if msg.timestamp:
        logical_clock = max(logical_clock, msg.timestamp) + 1
    
    # Armazenamento simples: aceita qualquer ordem
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)
    
    print(f"Evento processado: {msg.evtId}")
    showFeed() # Atualiza visualização

def showFeed():
    print("\n--- FEED ATUAL ---")
    # Imprime posts conhecidos
    for pid, post in posts.items():
        print(f"POST [{post.timestamp}] {post.author}: {post.text} (ID: {post.evtId})")
        # Imprime replies deste post
        if pid in replies:
            for r in replies[pid]:
                print(f"   -> REPLY [{r.timestamp}] {r.author}: {r.text}")
    
    print("\n--- REPLIES ÓRFÃS ---")
    # Verifica replies cujo pai não está em posts 
    for parent_id, reply_list in replies.items():
        if parent_id not in posts:
            for r in reply_list:
                print(f"   [ÓRFÃ] (Parent: {parent_id}) -> {r.author}: {r.text}")
    print("------------------\n")

# --- Endpoints HTTP ---

@app.post("/post") 
def post(msg: Event):
    global logical_clock
    
    # Se gerado localmente 
    if msg.processId == myProcessId:
        logical_clock += 1 # Incrementa relógio 
        msg.timestamp = logical_clock # Atribui timestamp
        
        # Processa localmente
        processMsg(msg)
        
        # Reencaminha 
        async_send(msg.dict())
        
    return {"status": "posted", "timestamp": logical_clock}

@app.post("/share") 
def share(msg: Event):
    # Processa evento recebido 
    processMsg(msg)
    return {"status": "received"}

# --- Inicialização ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python twitter_eventual.py <processId>")
        sys.exit(1)
        
    myProcessId = int(sys.argv[1])
    port = 8080 + myProcessId
    
    print(f"Iniciando Processo {myProcessId} na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
