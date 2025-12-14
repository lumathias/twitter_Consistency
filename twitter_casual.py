from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import threading
import time
import sys
import uvicorn
import requests

app = FastAPI()

# --- Estado global ---
myProcessId = 0
NUM_PROCESSES = 3

# Relógio Vetorial
vector_clock = [0] * NUM_PROCESSES 

posts = {}
replies = defaultdict(list)
message_buffer = [] # Buffer para mensagens fora de ordem

processes = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082"
]

class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    timestamp: List[int] # Vetor de inteiros para Causal

# --- Rede ---
def send_thread(url, payload):
    try:
        # Delay simulado para forçar causalidade invertida em testes
        if myProcessId == 0: time.sleep(3) 
        requests.post(f"{url}/share", json=payload, timeout=5)
    except Exception:
        pass

def async_send(payload: dict):
    for i, url in enumerate(processes):
        if i != myProcessId:
            t = threading.Thread(target=send_thread, args=(url, payload))
            t.start()

# --- Lógica Causal ---

def can_deliver(msg: Event) -> bool:
    """
    Verifica se a mensagem pode ser entregue garantindo Causalidade.
    1. Dependência de dados: Se for reply, o pai DEVE existir.
    2. Dependência temporal: Vector Clocks (opcional se a regra 1 for suficiente para o escopo, 
       mas implementado aqui para completude).
    """
    sender_id = msg.processId
    
    # 1. Checagem de dependência direta (Replies não podem ser órfãs)
    if msg.parentEvtId is not None:
        if msg.parentEvtId not in posts:
            return False # Pai ainda não chegou

    # 2. Checagem de Vetor (Protocolo de Broadcast Causal padrão)
    # Condição 1: A msg é a próxima esperada desse remetente? (V_msg[j] == V_local[j] + 1)
    is_next = msg.timestamp[sender_id] == vector_clock[sender_id] + 1
    
    # Condição 2: Já vimos tudo o que o remetente viu dos outros? (V_msg[k] <= V_local[k])
    seen_others = True
    for k in range(NUM_PROCESSES):
        if k != sender_id:
            if msg.timestamp[k] > vector_clock[k]:
                seen_others = False
                break
                
    return is_next and seen_others

def try_deliver_buffer():
    """Tenta entregar mensagens que estavam esperando no buffer."""
    global message_buffer
    progress = True
    while progress:
        progress = False
        remaining = []
        for msg in message_buffer:
            if can_deliver(msg):
                deliver(msg)
                progress = True
            else:
                remaining.append(msg)
        message_buffer = remaining

def deliver(msg: Event):
    global vector_clock
    # Incrementa o relógio local com base no remetente
    vector_clock[msg.processId] += 1
    
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)
    
    print(f"ENTREGUE: {msg.evtId} | Clock: {vector_clock}")
    showFeed()

def processMsg(msg: Event):
    # Ao receber mensagem remota
    if can_deliver(msg):
        deliver(msg)
        try_deliver_buffer()
    else:
        print(f"BUFFERIZADO: {msg.evtId} (Aguardando dependências...)")
        message_buffer.append(msg)

def showFeed():
    print(f"\n--- FEED (Clock: {vector_clock}) ---")
    sorted_posts = sorted(posts.values(), key=lambda x: x.timestamp) # Ordena visualmente
    for post in sorted_posts:
        print(f"POST {post.author}: {post.text} (ID: {post.evtId}) {post.timestamp}")
        if post.evtId in replies:
            for r in replies[post.evtId]:
                print(f"   -> REPLY {r.author}: {r.text} {r.timestamp}")
    print(f"Buffer size: {len(message_buffer)}")
    print("------------------\n")

# --- Endpoints ---

@app.post("/post")
def post(msg: Event):
    global vector_clock
    if msg.processId == myProcessId:
        # Atualiza vetor local antes de enviar
        vector_clock[myProcessId] += 1
        # Copia o vetor atual para a mensagem
        msg.timestamp = list(vector_clock)
        
        # Aplica localmente imediatamente (causalidade local é garantida)
        if msg.parentEvtId is None:
            posts[msg.evtId] = msg
        else:
            replies[msg.parentEvtId].append(msg)
            
        print(f"CRIADO LOCAL: {msg.evtId}")
        showFeed()
        async_send(msg.dict())
        
    return {"status": "posted", "clock": vector_clock}

@app.post("/share")
def share(msg: Event):
    processMsg(msg)
    return {"status": "received"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python twitter_causal.py <processId>")
        sys.exit(1)
        
    myProcessId = int(sys.argv[1])
    port = 8080 + myProcessId
    print(f"Iniciando Causal Node {myProcessId} na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
