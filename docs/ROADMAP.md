# Roteiro de Desenvolvimento (ROADMAP) — VÉSPERA

Este documento registra o status de implementação de cada uma das 5 fases obrigatórias do projeto.

---

## 📌 Status Atual: **Fase 1 — Fundação (Em Execução)**

---

## 🔬 Fase 1 — Fundação (MVP)
- [x] Concepção arquitetural, documentação de regras e modelo de dados.
- [ ] Estrutura inicial do repositório backend/frontend.
- [ ] Motor de simulação em Python puro isolado de frameworks web.
- [ ] Indexador espacial 2D (*Spatial Hash Grid*) com consultas $O(1)$ médio.
- [ ] Entidades `Organism` e `Food` com cinemática de Euler e física de bordas elásticas.
- [ ] Sistema de percepção e navegação (*Steering Behavior* com Wander e Seek).
- [ ] Balanço metabólico completo (custo basal, cinético e sensorial, morte por inanição e senescência).
- [ ] Bateria de testes automatizados com Pytest (invariantes de energia, colisão, limites e determinismo PRNG).
- [ ] Servidor FastAPI com endpoints REST e canal WebSocket para transmissão de estado.
- [ ] Interface React + Vite + TypeScript com renderização fluida em HTML5 Canvas 2D.
- [ ] Controles interativos de execução (`Play`, `Pause`, `Step`, `Reset`, `TPS Speed Slider`).
- [ ] Painel com telemetria básica em tempo real.

**Critério de Conclusão da Fase 1:** Executar a simulação de ponta a ponta, visualizando os organismos navegando fluidamente no Canvas, alimentando-se e morrendo de acordo com as regras determinísticas estabelecidas.

---

## 🧬 Fase 2 — Reprodução e Evolução
- [ ] Mecânica de reprodução assexuada/sexuada condicionada a limite de energia ($E > E_{reproduce}$).
- [ ] Divisão de biomassa/energia entre progenitor(es) e descendente(s).
- [ ] Genoma explícito: velocidade máxima, tamanho físico, raio de visão, cor e taxa metabólica.
- [ ] Algoritmo de mutação com desvio padrão configurável ($\mu, \sigma$).
- [ ] Identificador de linhagem e rastreamento de gerações ($gen$).
- [ ] Registro histórico de nascimentos, mortes naturais e mortes por inanição.

**Critério de Conclusão da Fase 2:** Demonstrar seleção natural observável, comprovando que organismos com traços mais adaptados ao ambiente persistem por mais gerações.

---

## 🐺 Fase 3 — Ecossistema Complexo
- [ ] Introdução da guilda de Predadores (carnívoros) e Presas (herbívoros).
- [ ] Dinâmica de perseguição (*Pursuit*) e evasão (*Flee/Evade*).
- [ ] Equações de equilíbrio populacional (estilo Lotka-Volterra emergente).
- [ ] Zonas ambientais (biomas com taxas variáveis de regeneração e atrito).
- [ ] Flutuações sazonais de recursos e eventos de seca/abundância.
- [ ] Indicadores matemáticos de estabilidade ecossistêmica e risco de extinção em cascata.

---

## 📊 Fase 4 — Laboratório de Experimentos
- [ ] Persistência completa com SQLite e SQLAlchemy no backend.
- [ ] Criação, salvamento e carregamento de ensaios com controle de semente PRNG.
- [ ] Coleta e agregação de séries temporais históricas em `tick_metrics`.
- [ ] Gráficos interativos com Recharts no frontend (População vs Tempo, Dispersão de Traços, Pirâmide Etária).
- [ ] Comparador de múltiplos experimentos lado a lado.
- [ ] Exportação de relatórios analíticos em JSON e CSV.

---

## ⏳ Fase 5 — Recursos Avançados
- [ ] Árvore genealógica interativa (filogenia) com visualização em grafos.
- [ ] Sistema de Snapshots comprimidos para "Viagem no Tempo" e exploração de cenários contrafactuais.
- [ ] Editor dinâmico de leis ambientais com limites estritos de segurança.
- [ ] Otimizações numéricas e vetorizadas para suportar mais de 5.000 organismos simultâneos.
