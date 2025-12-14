# Consistência de Dados em Sistemas Distribuídos

## Twitter com Consistência Eventual e Causal

**Autor(a):** Luisa M. G. Mathias

**Disciplina:** Sistemas Distribuídos (DCA3704)

**Curso:** Engenharia da Computação

**Instituição:** Universidade Federal do Rio Grande do Norte (UFRN)

-----

O sistema consiste em uma simulação de uma rede social (Twitter) implementada em **Python** utilizando **FastAPI**. O projeto demonstra na prática a diferença entre dois modelos de consistência de dados ao lidar com latência de rede e entrega de mensagens fora de ordem.


## Algoritmos Implementados

1.  **Consistência Eventual:**

      * Utiliza *Relógios Lógicos Simples (Lamport)* para ordenação básica.
      * As mensagens são entregues assim que chegam ao nó.
      * **Comportamento:** Permite a exibição de "Replies Órfãs" (respostas que chegam antes da postagem original). A convergência ocorre eventualmente quando todas as mensagens chegam.

2.  **Consistência Causal:**

      * Utiliza *Relógios Vetoriais (Vector Clocks)* para rastrear dependências causais.
      * Implementa um *Buffer de Mensagens* para reter eventos que chegaram fora de ordem.
      * **Comportamento:** Garante que uma resposta só seja visível após a chegada do post original, respeitando a relação de causa e efeito.

-----

## Como Executar (Google Cloud Shell)

### 1. Preparar o Ambiente

Abra o terminal do Cloud Shell e instale as dependências necessárias:

```bash
pip install fastapi uvicorn requests
```

### 2. Estratégia de Terminais

Para simular o sistema distribuído, você precisará de **4 abas de terminal** abertas simultaneamente:

  * **Terminais 1, 2 e 3:** Rodarão as instâncias (nós) do servidor.
  * **Terminal 4:** Será usado como cliente para enviar comandos `curl`.

### 3. Iniciar os Servidores

Escolha qual versão deseja rodar (Eventual ou Causal) e execute os comandos abaixo, um em cada terminal correspondente:

| Terminal | Comando (Versão Eventual) | Comando (Versão Causal) | Porta |
| :--- | :--- | :--- | :--- |
| **Aba 1** | `python twitter_eventual.py 0` | `python twitter_causal.py 0` | 8080 |
| **Aba 2** | `python twitter_eventual.py 1` | `python twitter_causal.py 1` | 8081 |
| **Aba 3** | `python twitter_eventual.py 2` | `python twitter_causal.py 2` | 8082 |

> **Nota:** Para trocar de versão, pare os processos atuais com `Ctrl+C` antes de iniciar os novos.

-----

## Roteiro de Testes (Demonstração)

Utilize a **Aba 4** para enviar as requisições. O cenário simula um atraso no **Nó 0**, fazendo com que uma resposta enviada diretamente ao **Nó 2** chegue antes do post original.

### Cenário 1: Testando Consistência Eventual

Certifique-se de que está rodando `twitter_eventual.py`.

1.  **Postar no Nó 0 (Lento):**

    ```bash
    curl -X POST "http://localhost:8080/post" -H "Content-Type: application/json" -d '{"processId": 0, "evtId": "p1", "author": "Alice", "text": "Post Original", "timestamp": null}'
    ```

2.  **Responder Imediatamente no Nó 2:**

    ```bash
    curl -X POST "http://localhost:8082/post" -H "Content-Type: application/json" -d '{"processId": 2, "evtId": "r1", "parentEvtId": "p1", "author": "Bob", "text": "Resposta Rapida", "timestamp": null}'
    ```

**Verificação (Olhe o Terminal do Nó 2):**

  * O sistema exibirá imediatamente: `[ÓRFÃ] (Parent: p1) -> Bob: Resposta Rapida`.
  * Isso prova que a consistência foi quebrada momentaneamente (efeito antes da causa).

### Cenário 2: Testando Consistência Causal

Pare os processos anteriores e inicie `twitter_causal.py`.

1.  **Postar no Nó 0 (Lento):**

    ```bash
    curl -X POST "http://localhost:8080/post" -H "Content-Type: application/json" -d '{"processId": 0, "evtId": "pc1", "author": "Alice", "text": "Post Causal", "timestamp": []}'
    ```

2.  **Responder Imediatamente no Nó 2:**

    ```bash
    curl -X POST "http://localhost:8082/post" -H "Content-Type: application/json" -d '{"processId": 2, "evtId": "rc1", "parentEvtId": "pc1", "author": "Bob", "text": "Resposta Causal", "timestamp": []}'
    ```

**Verificação (Olhe o Terminal do Nó 2):**

  * O sistema exibirá: `BUFFERIZADO: rc1`. A mensagem de Bob **não** aparece no feed.
  * Após alguns segundos, quando a mensagem de Alice chega, ambas aparecem na ordem correta:
    1.  `POST Alice: Post Causal`
    2.  `-> REPLY Bob: Resposta Causal`

-----

## Tecnologias

  * **Python 3**
  * **FastAPI:** Framework Web Assíncrono
  * **Uvicorn:** Servidor ASGI
  * **Requests:** Cliente HTTP
  * **Threading:** Concorrência para envio de mensagens
-----

## Referências

  * Arquivo de especificação do projeto: `consistência.pdf`.
  * Tanenbaum, A. S., & Van Steen, M. (2017). *Distributed Systems* (3ª Ed.).
  * Lamport, L. (1978). "Time, Clocks, and the Ordering of Events in a Distributed System".

-----
