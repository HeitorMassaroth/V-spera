# VÉSPERA — Simulador de Vida Artificial & Ecossistemas Computacionais

[![CI](https://github.com/HeitorMassaroth/V-spera/actions/workflows/ci.yml/badge.svg)](https://github.com/HeitorMassaroth/V-spera/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **VÉSPERA** é um laboratório interativo de vida artificial voltado para a experimentação de ecossistemas virtuais nos quais organismos autônomos sobrevivem, exploram o ambiente, alimentam-se, dissipam energia termodinâmica e evoluem ao longo das gerações por meio de dinâmicas emergentes e verificáveis.

---

## 🧭 Visão do Projeto

O objetivo do VÉSPERA não é ser um jogo nem uma simples animação gráfica, mas um **software científico e experimental sólido**. Todas as dinâmicas emergem de leis matemáticas explícitas:

- **Cinemática Newtoniana & Steering Behaviors:** Navegação suave via forças de Reynolds (*Seek* e *Wander* temporalmente coerente).
- **Indexação Espacial em $O(1)$ Médio:** Utilização de *Spatial Hash Grid* para eliminar a degradação quadrática $O(N^2)$ típica de simulações com centenas de partículas.
- **Balanço Metabólico Termodinâmico:** Custo basal proporcional ao tamanho/volume, custo cinético quadrático dependente da velocidade ($\propto v^2$) e custo sensorial de percepção.
- **Determinismo Estrito:** Controle rigoroso de geradores pseudoaleatórios (PRNG isolado por experimento) garantindo reprodutibilidade bit a bit com a mesma semente.
- **Arquitetura Limpa:** Desacoplamento total entre o núcleo da simulação (`core/`), a camada de rede/serviço (`engine/` + `api/`) e a interface gráfica (`frontend/`).

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Justificativa Técnica |
| :--- | :--- | :--- |
| **Motor da Simulação** | Python puro | Portabilidade, ausência de acoplamento a frameworks e legibilidade matemática. |
| **Indexador Espacial** | Spatial Hash Grid 2D | Consultas de vizinhança e recursos em tempo constante $O(1)$ médio. |
| **API & Streaming** | FastAPI + WebSockets | Baixa latência, validação estrita via Pydantic e streaming de alta frequência. |
| **Persistência Relacional** | SQLite (Modo WAL) + SQLAlchemy 2.0 | Gravação econômica de metadados, checkpoints comprimidos e séries temporais. |
| **Frontend** | React 19 + TypeScript + Vite | Tipagem segura espelhando os DTOs do backend e build instantâneo. |
| **Renderização do Mundo** | HTML5 Canvas 2D | Desempenho de 60 FPS com Pan & Zoom, desacoplado do relógio físico do servidor. |
| **Telemetria** | Sparklines SVG dinâmicas | Leveza, responsividade e zero dependências pesadas na telemetria básica. |
| **Qualidade & Testes** | Pytest + AsyncIO | Testes unitários, invariantes de energia, testes de determinismo e extinção. |

---

## 📂 Estrutura do Repositório

```
V-spera/
├── backend/
│   ├── src/
│   │   ├── core/                       # Núcleo puro da simulação (Zero dependências web)
│   │   │   ├── entities/               # Organism, Food, OrganismTraits
│   │   │   ├── spatial/                # SpatialHashGrid (O(1) médio)
│   │   │   ├── systems/                # MovementSystem, MetabolismSystem, PerceptionSystem
│   │   │   ├── prng.py                 # Gerador determinístico encapsulado
│   │   │   └── world.py                # Ecossistema 2D e relógio discreto
│   │   ├── engine/                     # SimulationRunner e loop assíncrono
│   │   ├── infrastructure/             # SQLite WAL, SQLAlchemy e modelos ORM
│   │   ├── api/                        # FastAPI routers, schemas Pydantic e WebSocket
│   │   └── main.py                     # Entry point do servidor
│   ├── tests/
│   │   ├── unit/                       # Testes de cinemática, metabolismo e grid
│   │   ├── simulation/                 # Testes de determinismo SHA-256 e extinção
│   │   └── integration/                # Testes de integração da API REST
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── canvas/WorldRenderer.ts     # Motor de renderização em Canvas 2D
│   │   ├── components/                 # TopBar, SimulationViewer, MetricsPanel, ConfigModal
│   │   ├── hooks/useSimulationSocket.ts# Conexão reativa WebSocket
│   │   └── types.ts                    # Tipos TypeScript espelhados
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md                 # Decisões arquiteturais detalhadas
│   ├── SIMULATION_RULES.md             # Equações matemáticas e regras
│   ├── DATA_MODEL.md                   # Persistência e dados
│   └── ROADMAP.md                      # Fases 1 a 5 de desenvolvimento
├── BUGS_E_MELHORIAS.md                 # Rastreamento de bugs, riscos e melhorias futuras
└── README.md
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- **Python 3.11+**
- **Node.js 18+** e **npm**

### 1. Inicializando o Backend

```bash
# Entre na pasta backend
cd backend

# Crie e ative o ambiente virtual
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Linux/macOS:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Inicie o servidor FastAPI na porta 8000
python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000
```

A documentação interativa Swagger estará disponível em: `http://127.0.0.1:8000/docs`

### 2. Inicializando o Frontend

```bash
# Em outro terminal, entre na pasta frontend
cd frontend

# Instale as dependências
npm install

# Inicie o servidor Vite na porta 5173
npm run dev
```

Abra no seu navegador: **`http://127.0.0.1:5173/`**

---

## 🧪 Executando os Testes Automatizados

O VÉSPERA conta com uma suíte de testes rigorosa que valida não apenas a integridade do código, mas também as propriedades científicas do modelo:

```bash
cd backend
.venv\Scripts\activate
pytest tests/ -v
```

### O que os testes verificam:
1. **Determinismo Estrito (`test_determinism.py`):** Valida que duas execuções com a mesma semente PRNG geram exatamente o mesmo estado após centenas de ticks (hash SHA-256 idêntico do snapshot).
2. **Extinção Controlada (`test_extinction.py`):** Comprova que um ecossistema sem alimento ($R_{spawn}=0$) sofre extinção por inanição dentro do teto teórico de tempo.
3. **Consistência Espacial (`test_spatial_grid.py`):** Valida que o *Spatial Hash Grid* retorna os mesmos candidatos que uma busca por força bruta $O(N^2)$, porém em tempo constante médio.
4. **Balanço Energético (`test_metabolism.py`):** Dedução exata dos custos metabólicos basais, cinéticos e sensoriais.
5. **Integração REST e WebSocket (`test_api.py`):** Fluxo completo de controle de simulação via HTTP/WS.

---

## 🎮 Controles e Atalhos

| Comando | Atalho | Ação |
| :--- | :---: | :--- |
| **Iniciar / Pausar** | `Espaço` | Alterna entre execução contínua e pausa. |
| **Avanço Passo a Passo** | `.` (Ponto) | Avança exatamente 1 tick para inspeção. |
| **Reiniciar** | `R` | Reinicia a simulação com a semente configurada. |
| **Pan (Mover Mundo)** | `Clique + Arraste` | Movimenta a câmera pelo ecossistema. |
| **Zoom In / Out** | `Scroll do Mouse` | Aproxima ou afasta o campo visual. |
| **Ajuste de Velocidade** | Slider na barra | Regula a taxa de 5 a 60 ticks por segundo (TPS). |
| **Camadas de Debug** | Botões no Canvas | Alterna raios sensoriais, vetores de velocidade e grade espacial. |

---

## 🗺️ Roadmap das Fases

- [x] **Fase 1 — Fundação:** Motor isolado, física 2D, cinemática de Reynolds, Spatial Hash Grid, balanço metabólico, API FastAPI, WebSocket, persistência SQLite e interface Canvas 2D.
- [ ] **Fase 2 — Reprodução e Evolução:** Herança genética de traços, mutações parametrizáveis e controle de linhagens/gerações.
- [ ] **Fase 3 — Ecossistema Complexo:** Predadores e presas (herbívoros/carnívoros), evasão e equilíbrio populacional.
- [ ] **Fase 4 — Laboratório de Experimentos:** Ensaios comparativos, gráficos analíticos com Recharts e exportação de relatórios.
- [ ] **Fase 5 — Recursos Avançados:** Árvore filogenética, snapshots de viagem no tempo e editor dinâmico de regras.

---

## 📄 Licença
Distribuído sob a licença MIT. Consulte `LICENSE` para mais detalhes.