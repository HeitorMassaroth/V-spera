# Modelo de Persistência e Dados — VÉSPERA

## 1. Princípios de Modelagem

O sistema separa estritamente o estado volátil de alta frequência (*Hot State*) do estado histórico e analítico persistente (*Cold State*).

```
[Memória Volátil (RAM)]                         [Banco Relacional (SQLite WAL)]
Organisms (x, y, vx, vy, E) ---- Agregação ---> TickMetrics (avg_energy, pop, food)
Food (x, y, energy)         ---- Snapshots ---> SimulationSnapshots (zlib binary state)
                                                Experiments (seeds, params, status)
```

---

## 2. Tabelas Relacionais

### 2.1 Tabela `experiments`
Armazena a definição formal de cada ensaio científico, permitindo rastrear condições de contorno e reprodutibilidade.

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `VARCHAR(36)` (PK) | UUID identificador do experimento. |
| `name` | `VARCHAR(100)` | Nome descritivo dado pelo pesquisador. |
| `description` | `TEXT` | Hipótese ou objetivo do experimento. |
| `seed` | `BIGINT` | Semente do gerador pseudo-aleatório (PRNG). |
| `world_width` | `FLOAT` | Largura do ambiente em pixels/unidades. |
| `world_height`| `FLOAT` | Altura do ambiente em pixels/unidades. |
| `initial_population` | `INTEGER` | População inicial introduzida. |
| `initial_food` | `INTEGER` | Quantidade inicial de alimento. |
| `food_spawn_rate` | `FLOAT` | Taxa de renovação de recursos por tick. |
| `max_food` | `INTEGER` | Capacidade de suporte de recursos no ambiente. |
| `created_at` | `DATETIME` | Data e hora de criação. |
| `status` | `VARCHAR(20)` | `RUNNING`, `PAUSED`, `EXTINCT`, `COMPLETED`. |

### 2.2 Tabela `tick_metrics`
Registra a evolução temporal em intervalos regulares (ex.: a cada 20 ticks) para alimentar os gráficos de telemetria sem sobrecarregar o disco.

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK, Auto) | Identificador do registro. |
| `experiment_id` | `VARCHAR(36)` (FK) | Vínculo com a tabela `experiments`. |
| `tick` | `BIGINT` | Ciclo temporal correspondente. |
| `population_count` | `INTEGER` | Número de organismos vivos. |
| `food_count` | `INTEGER` | Quantidade de recursos disponíveis. |
| `average_energy` | `FLOAT` | Média de energia da população viva. |
| `max_energy` | `FLOAT` | Maior reserva de energia encontrada. |
| `births_count` | `INTEGER` | Nascimentos ocorridos no intervalo. |
| `deaths_count` | `INTEGER` | Mortes ocorridas no intervalo. |
| `average_speed` | `FLOAT` | Média da velocidade dos indivíduos. |
| `average_vision` | `FLOAT` | Média do raio de visão dos indivíduos. |

### 2.3 Tabela `simulation_snapshots`
Salva estados completos da simulação de forma comprimida para permitir a retomada (*checkpointing*) e "viagem no tempo" (Fase 5).

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK, Auto) | Identificador do snapshot. |
| `experiment_id` | `VARCHAR(36)` (FK) | Vínculo com a tabela `experiments`. |
| `tick` | `BIGINT` | Ciclo exato do snapshot. |
| `prng_state` | `TEXT` | Estado interno do gerador aleatório serializado. |
| `compressed_state` | `BLOB` | JSON serializado de todas as entidades comprimido via zlib. |
| `created_at` | `DATETIME` | Timestamp de geração. |
