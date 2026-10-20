# 📋 Diagnóstico, Bugs & Melhorias Futuras — VÉSPERA
*Documento vivo de rastreamento de qualidade, pontos de atenção e roteiro de evolução contínua da simulação.*

**Última Atualização:** Outubro de 2026  
**Branch Atual:** `feature/natural-genesis-pioneers`  
**Status da Suíte de Testes:** 128/128 Testes Aprovados (`pytest`) • Build Frontend OK

---

## 🧭 Sumário Executivo do Estado Atual

O ecossistema **VÉSPERA** atingiu um estado de alta maturidade arquitetural e fidelidade biológica:
- **Gênese Primordial Natural:** O mundo inicia com sorteio determinístico de 0 a 10 indivíduos pioneiros para cada sexo (Macho e Fêmea) de cada espécie (Predadores e Vrancos).
- **Sem Geração Espontânea:** Zero ninhos e zero clãs pré-fabricados. Toda e qualquer reprodução exige encontro, compatibilidade, corte, vínculo monogâmico e dois pais biológicos comprovados na árvore genealógica.
- **Ecologia Dinâmica Integrada:** 4 estações climáticas com partículas dinâmicas no Canvas, 8 zonas territoriais com pontuação ecológica, dinâmica de clãs com liderança Alpha/Beta, moral e diplomacia (Aliança, Trégua, Neutralidade, Guerra).
- **Crônica Histórica Causal:** Registro centralizado com busca, causalidade de eventos e preservação de memória.

Abaixo estão catalogados os **pontos de atenção/bugs potenciais** e o **roteiro detalhado de melhorias técnicas e visuais**.

---

## 🐛 1. Bugs Diagnosticados & Soluções Implementadas

| ID | Área | Descrição / Risco | Severidade | Status & Solução Implementada |
|---|---|---|---|---|
| **BUG-01** | *Gênese / Demografia* | **Assimetria de Sexos na Gênese (0 a 10):** Se o RNG sorteasse apenas machos ou apenas fêmeas de uma espécie pioneira, haveria colapso precoce sem chance reprodutiva. | 🟡 Média | ✅ **RESOLVIDO:** Implementado balanceador biológico em `World.__init__`: caso uma espécie surja na gênese (`> 0`), o sexo oposto é garantido com pelo menos 1 indivíduo (`randint(1, min(10, n))`), assegurando viabilidade de acasalamento sem perder a aleatoriedade. Validado com 50 sementes contínuas em `test_sexual_viability_pioneers`. |
| **BUG-02** | *Ecologia / Recursos* | **Hiperabundância Vegetal Inicial:** Populações pioneiras reduzidas (ex: 2 a 4 indivíduos) sofriam com excesso imediato de comida acumulada no mapa. | 🟢 Baixa | ✅ **RESOLVIDO:** Alimento inicial agora escala proporcionalmente à população pioneira (`min(initial_food, max(16, pioneers * 4))`). No loop de ticks, a taxa de spawn aplica feedback populacional (`pop_ratio`) e saturação logística quadrática ao se aproximar de `max_food`. |
| **BUG-03** | *Performance / Backend* | **Crescimento de Árvore Genealógica em Sessões Ultralongas:** Em sessões com > 50.000 ticks, o grafo genealógico em memória crescia sem limite de descarte. | 🟡 Média | ✅ **RESOLVIDO:** Implementado algoritmo `prune_ancient_records` em `GenealogyRegistry` e disparado a cada 250 ticks. Preserva com precisão cirúrgica todos os indivíduos vivos, pioneiros fundadores (G0) e ancestrais diretos até 6 graus de parentesco (profundidade de Wright/Malécot), podando com segurança registros mortos desconectados. Validado em `test_genealogy_prune_ancient_records`. |
| **BUG-04** | *Canvas / Frontend* | **Display High-DPI (Retina / 4K):** Telas com `devicePixelRatio > 1` sofriam leve perda de nitidez ou custo com recálculo síncrono de DOM (`getBoundingClientRect`) 60x por segundo. | 🟢 Baixa | ✅ **RESOLVIDO:** `WorldRenderer` agora gerencia propriedade `dpr` nativa com `ctx.scale(dpr, dpr)`. Em `SimulationViewer.tsx`, as dimensões são cacheadas em `dimensionsRef`, eliminando os 60 reflows de layout por segundo e garantindo nitidez cristalina em monitores 4K. |
| **BUG-05** | *WebSocket / Rede* | **Reconexão Rápida sob Queda de Conexão:** Quedas temporárias de rede deixavam o status silencioso ou exigiam refresh manual. | 🟢 Baixa | ✅ **RESOLVIDO:** `useSimulationSocket` agora possui backoff progressivo (1s a 3.5s), estado `isReconnecting` e método manual `reconnect`. A `TopBar` exibe badge interativo animado com botão direto `[Reconectar]`. |

---

## 🚀 2. Melhorias Recomendadas por Módulo

### 2.1 Backend & Motor da Simulação (`backend/`)
- [ ] **Spawn de Comida Dinâmico Proporcional (Feedback Regulatório):**
  - Ajustar o multiplicador de geração de alimento para responder à biomassa vegetal não consumida, simulando esgotamento de solo e saturação ecológica natural.
- [ ] **Especialização Ocupacional nos Clãs:**
  - Além de Alpha e Beta, permitir que membros adultos assumam papéis emergentes baseados em personalidade e genoma:
    - *Guardião:* Indivíduos com alta Força patrulham as bordas do ninho.
    - *Coletor:* Indivíduos rápidos e sociáveis priorizam transporte de comida comunitária.
    - *Nutriz:* Fêmeas mais carinhosas e dóceis cuidam dos filhotes de outras famílias do clã durante o inverno.
- [ ] **Patologias & Imunidade Genética:**
  - Traço genético de resistência imunológica. Regiões territoriais degradadas ou com superpopulação passam a ter probabilidade de surgimento de agentes infecciosos sazonais.
- [ ] **Persistência em Disco SQLite / ZSTD:**
  - Adicionar opção de salvar o snapshot atual do mundo em arquivo `.bin` ou banco local SQLite, permitindo carregar ensaios científicos anteriores.
- [ ] **Otimizações Cinemáticas:**
  - Vetorização do cálculo de forças de repulsão de colisão entre organismos para sustentar > 1.000 organismos simultâneos a 60 TPS sem perda de taxa de quadros.

---

### 2.2 Visual, Canvas & Frontend (`frontend/`)
- [ ] **Árvore Genealógica Interativa em Grafo (Filogenia Visual):**
  - Componente com visualização tipo árvore hierárquica (estilo D3 ou SVG/Canvas) permitindo clicar em qualquer indivíduo e rastrear linhagem paterna/materna, mutações acumuladas e coeficiente de consanguinidade até os pioneiros.
- [ ] **Mini-Mapa / Radar Ecológico:**
  - Inserir no canto inferior direito do canvas um mini-radar translúcido exibindo a localização relativa dos territórios, oásis de clãs e concentrações populacionais.
- [ ] **Gráficos de Dispersão Fenotípica em Tempo Real:**
  - Gráfico de dispersão 2D interativo no painel de evolução: Eixo X (Velocidade) vs Eixo Y (Força), permitindo visualizar a especiação morfológica ao longo das gerações.
- [ ] **Efeitos Sonoros Biológicos Procedurais (Web Audio API):**
  - Síntese de áudio leve e nativa (sem arquivos pesados de áudio) para eventos marcantes:
    - Piado suave de filhote no nascimento.
    - Impacto abafado em disputas territoriais.
    - Sussurro de vento suave na mudança de estação climática.
- [ ] **Controle de Câmera Suave (Cinematic Auto-Tracking):**
  - Modo "Câmera de Documentário" que seleciona automaticamente o habitante envolvido no evento mais dramático do momento (ex: caçada de predador, nascimento ou duelo de líderes).

---

### 2.3 Interface do Usuário & Análise (`MetricsPanel.tsx` & `ControlBar.tsx`)
- [ ] **Exportação de Dados da Simulação:**
  - Botão para exportar séries temporais completas em formato `.csv` ou `.json` (população por espécie, biomassa vegetal, médias genéticas por tick).
- [ ] **Filtros Avançados na Linha do Tempo da Crônica:**
  - Filtro por dinastia/linhagem fundadora e busca textual instantânea por palavras-chave em causas e resultados históricos.
- [ ] **Painel de Comparação de Gerações:**
  - Comparar estatísticas da Geração 0 (Pioneiros Fundadores) com a Geração atual para evidenciar quantitativamente a seleção natural ocorrida.

---

## 📊 3. Matriz de Priorização (Esforço x Impacto)

```
        ▲ ALTO
        │  [Mini-Mapa Radar]                [Árvore Genealógica Interativa]
        │  [Spawn Proporcional de Comida]    [Especialização de Clãs]
IMPACTO │  
        │  [Exportação CSV/JSON]             [Persistência SQLite em Disco]
        │  [High-DPI Canvas Retina]          [Áudio Procedural WebAudio]
        ▼ BAIXO
        └─────────────────────────────────────────────────────────────►
          BAIXO                       ESFORÇO                      ALTO
```

---

## 📅 4. Roteiro de Execução Sugerido

### Sprint I — Estabilidade & Usabilidade (Imediato)
1. **DPI Scaling no Canvas:** Ajustar o `devicePixelRatio` para máxima definição em telas 4K.
2. **Exportação de Relatórios CSV/JSON:** Permitir download da crônica e histórico ecológico.
3. **Spawn Regulatório Proporcional:** Suavizar acúmulo de alimento quando a população pioneira for mínima.

### Sprint II — Visual & Telemetria Avançada (Médio Prazo)
1. **Mini-Mapa Radar:** Implementar radar no canto do Canvas com visualização global dos biomas.
2. **Árvore Genealógica em Grafo:** Navegador visual de linhagens ancestrais.
3. **Scatter Plot Fenotípico:** Gráfico de correlação entre atributos físicos no painel de evolução.

### Sprint III — Ecologia Profunda (Longo Prazo)
1. **Papéis Sociais Dinâmicos:** Guardiões, caçadores e nutrizes organizados por clã.
2. **Patologias e Resistência Genética:** Pressão seletiva ambiental adicional.
3. **Checkpoints Contínuos em Disco:** Sistema de *save/load* completo de cenários contrafactuais.
