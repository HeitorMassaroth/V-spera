# Arquitetura do Sistema VÉSPERA

## 1. Visão Geral e Filosofia de Design

O **VÉSPERA** é projetado sob os princípios de **Clean Architecture** (Arquitetura Limpa) e **Separação Estrita de Responsabilidades** (*Separation of Concerns*). O motor computacional da simulação é completamente desacoplado de qualquer tecnologia de entrega (HTTP, WebSocket) ou de persistência (Banco de Dados).

```
                      +---------------------------------------+
                      |               Frontend                |
                      |    (React, TypeScript, Canvas 2D)     |
                      +-------------------+-------------------+
                                          |
                                          | WebSocket (Streaming) & REST
                                          v
                      +---------------------------------------+
                      |               API Layer               |
                      |          (FastAPI, Pydantic)          |
                      +-------------------+-------------------+
                                          |
                                          | Orquestração
                                          v
                      +---------------------------------------+
                      |            Engine Runner              |
                      |        (Task / Thread de Loop)        |
                      +-------------------+-------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
+---------------------------------------+   +---------------------------------------+
|            Simulation Core            |   |             Persistência              |
|        (Python Puro, O(1) Grid)       |   |          (SQLite WAL, Alembic)        |
| - Entidades (Organismos, Comida)      |   | - Experimentos e Parâmetros           |
| - Sistemas (Metabolismo, Cinemática)  |   | - Snapshots Periódicos de Estado      |
| - Espaço e PRNG Determinístico        |   | - Séries Temporais de Métricas        |
+---------------------------------------+   +---------------------------------------+
```

---

## 2. Camadas do Sistema

### 2.1 Simulation Core (`backend/src/core/`)
- **Isolamento Tecnológico:** Não contém dependências de frameworks externos (sem FastAPI, sem SQLAlchemy).
- **Relógio Discreto:** O tempo avança em unidades discretas de ciclo ($\Delta t = 1 \text{ tick}$).
- **Determinismo Estrito:** Todo número pseudo-aleatório é obtido de uma instância isolada de gerador (`Random` ou `PCG64`), permitindo reprodução idêntica com a mesma semente (*seed*).
- **Indexação Espacial ($O(1)$ médio):** Utiliza um *Spatial Hash Grid* para particionar o espaço euclidiano $W \times H$. Organismos realizam consultas de raio de visão consultando apenas células adjacentes, eliminando a degradação $O(N^2)$ presente em algoritmos ingênuos.

### 2.2 Orquestrador da Execução (`backend/src/engine/`)
- Mantém o estado ativo do ecossistema e regula a velocidade de execução (TPS - *Ticks Per Second*).
- Suporta operações de controle de alto nível:
  - `play()`: Inicia o avanço contínuo dos ciclos.
  - `pause()`: Suspende a atualização temporal, mantendo o estado intacto.
  - `step()`: Avança exatamente 1 tick para inspeção cirúrgica de estados.
  - `reset(seed)`: Reinicia as entidades e o gerador aleatório.
  - `set_speed(tps)`: Ajusta a cadência do relógio (ex.: de 5 a 60 ticks por segundo).

### 2.3 Camada de Persistência (`backend/src/infrastructure/`)
- **Estratégia de Escrita Econômica:** O banco de dados **não** persiste a trajetória frame a frame de cada organismo. Em vez disso, grava:
  1. Metadados do experimento e parâmetros iniciais.
  2. Métricas agregadas a cada $N$ ciclos (população viva, energia total, média de idade, nascimentos, mortes).
  3. Snapshots completos comprimidos em intervalos esparsos ($K$ ticks) para permitir recuperação de estado e exploração de cenários.

### 2.4 Interface e Visualização (`frontend/`)
- **Renderização por Canvas 2D:** Renderização de alto desempenho em elemento `<canvas>` através de `requestAnimationFrame`.
- **Desacoplamento de Taxas:** A taxa de quadros visual (FPS, ~60 FPS) é desacoplada da taxa de simulação física (TPS), aplicando interpolação linear suave (*lerp*) entre os deltas recebidos via WebSocket.
- **Painéis Científicos:** Telemetria com séries temporais de indicadores e controles ergonomicamente isolados para experimentação.
