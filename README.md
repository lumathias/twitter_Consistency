# Twitter: Consistência Eventual vs. Causal

*Autor(a):** Luisa M. G. Mathias

**Disciplina:** Sistemas Distribuídos (DCA3704)

**Curso:** Engenharia da Computação

**Instituição:** Universidade Federal do Rio Grande do Norte (UFRN)


Este projeto implementa uma simulação simplificada de uma rede social distribuída (estilo Twitter) para demonstrar na prática a diferença entre **Consistência Eventual** e **Consistência Causal** em sistemas distribuídos.

O projeto consiste em três réplicas (processos) que se comunicam via HTTP.

## Estrutura do Projeto

  * `twitter_eventual.py`: Implementação usando Relógios Lógicos simples (Lamport). Permite que respostas ("replies") sejam exibidas antes do post original (inconsistência temporária).
  * `twitter_causal.py`: Implementação usando Relógios Vetoriais (Vector Clocks) e Buffer de Espera. Garante que uma resposta só seja entregue após a visualização do post original.

## Pré-requisitos

O projeto foi desenvolvido em **Python 3**. As seguintes bibliotecas são necessárias:

```bash
pip install fastapi uvicorn requests
```

## Como Rodar (Passo a Passo)

Para executar o sistema, você precisará de **4 terminais** abertos simultaneamente (3 para os servidores e 1 para enviar comandos).

### Cenário 1: Testando a Consistência Eventual

Neste cenário, vamos demonstrar uma **anomalia**: uma resposta aparecendo antes da pergunta.

1.  **Inicie os Servidores:**
    Abra 3 terminais e rode um comando em cada um:

      * Terminal 1: `python twitter_eventual.py 0`
      * Terminal 2: `python twitter_eventual.py 1`
      * Terminal 3: `python twitter_eventual.py 2`

2.  **Execute o Teste (Terminal 4):**
    No quarto terminal (livre), execute os comandos abaixo na ordem.

      * **Passo A: Postar no Nó 0 (Lento)**
        *O Nó 0 tem um delay simulado de 2 segundos para propagar a mensagem.*

        ```bash
        curl -X POST "http://localhost:8080/post" \
        -H "Content-Type: application/json" \
        -d '{"processId": 0, "evtId": "evt_1", "author": "Alice", "text": "Ola Mundo", "timestamp": null}'
        ```

      * **Passo B: Responder diretamente no Nó 2 (Rápido)**
        *Enviamos a resposta ao Nó 2 antes que a mensagem de Alice chegue lá.*

        ```bash
        curl -X POST "http://localhost:8082/post" \
        -H "Content-Type: application/json" \
        -d '{"processId": 2, "evtId": "reply_1", "parentEvtId": "evt_1", "author": "Bob", "text": "Oi Alice!", "timestamp": null}'
        ```

3.  **Verifique o Resultado (Terminal 3):**
    No terminal do Processo 2, você verá:

    > `[ÓRFÃ] (Parent: evt_1) -> Bob: Oi Alice!`

    Isso comprova a consistência eventual: a mensagem chegou, foi aceita, mas violou a ordem causal.

-----

### Cenário 2: Testando a Consistência Causal

Neste cenário, o sistema deve **impedir** a visualização da resposta até que a pergunta chegue.

1.  **Reinicie os Servidores:**

      * Vá nos Terminais 1, 2 e 3.
      * Pressione `Ctrl+C` para parar a versão eventual.
      * Inicie a versão causal:
          * Terminal 1: `python twitter_causal.py 0`
          * Terminal 2: `python twitter_causal.py 1`
          * Terminal 3: `python twitter_causal.py 2`

2.  **Execute o Teste (Terminal 4):**
    Note que o payload agora envia uma lista vazia `[]` no timestamp para inicialização vetorial.

      * **Passo A: Postar no Nó 0 (Lento)**

        ```bash
        curl -X POST "http://localhost:8080/post" \
        -H "Content-Type: application/json" \
        -d '{"processId": 0, "evtId": "causal_msg", "author": "Alice", "text": "Post Causal", "timestamp": []}'
        ```

      * **Passo B: Responder diretamente no Nó 2**

        ```bash
        curl -X POST "http://localhost:8082/post" \
        -H "Content-Type: application/json" \
        -d '{"processId": 2, "evtId": "causal_reply", "parentEvtId": "causal_msg", "author": "Bob", "text": "Resposta Causal", "timestamp": []}'
        ```

3.  **Verifique o Resultado (Terminal 3):**
    No terminal do Processo 2, observe o comportamento:

    1.  Assim que você envia o **Passo B**, ele exibe:
        > `BUFFERIZADO: causal_reply (Aguardando dependências...)`
    2.  O feed **não** mostra a resposta de Bob.
    3.  Após alguns segundos (quando a mensagem de Alice chega), ele exibe:
        > `ENTREGUE: causal_msg`
        > `ENTREGUE: causal_reply` (Desenfileirado automaticamente)

    Isso comprova a consistência causal: a ordem lógica foi respeitada.

##  Configuração de Portas

O sistema utiliza as seguintes portas padrão:

  * Processo 0: `8080`
  * Processo 1: `8081`
  * Processo 2: `8082`

Certifique-se de que estas portas estejam livres no seu ambiente.
