# 📋 Diagnóstico, Bugs & Melhorias Futuras — VÉSPERA
*Documento vivo de rastreamento de qualidade, pontos de atenção e roteiro de evolução contínua da s**Última Atualização:** Outubro de 2026  
**Branch Atual:** `feature/natural-genesis-pioneers`  
**Status da Suíte de Testes:** 132/132 Testes Aprovados (`pytest`) • Build Frontend OK (TypeScript & Vite)

---

## 🧭 Sumário Executivo do Estado Atual

O ecossistema **VÉSPERA** atingiu um estado de alta maturidade arquitetural e fidelidade biológica:
- **Gênese Primordial Natural:** O mundo inicia com sorteio determinístico de 0 a 10 indivíduos pioneiros para cada sexo (Macho e Fêmea) de cada espécie (Predadores e Vrancos).
- **Sem Geração Espontânea:** Zero ninhos e zero clãs pré-fabricados. Toda e qualquer reprodução exige encontro, compatibilidade, corte, vínculo monogâmico e dois pais biológicos comprovados na árvore genealógica.
- **Ecologia Dinâmica Integrada:** 4 estações climáticas com partículas dinâmicas no Canvas, 8 zonas territoriais com pontuação ecológica, dinâmica de clãs com liderança Alpha/Beta, moral e diplomacia (Aliança, Trégua, Neutralidade, Guerra).
- **Crônica Histórica Causal:** Registro centralizado com busca, causalidade de eventos e preservação de memória.
- **Especialização de Clãs:** Guardiões, Coletores e Nutrizes com fenótipos emergentes e insignias no Canvas.
- **Telemetria & Sensorialidade:** Mini-Mapa Radar translúcido no Canvas, sintetizador de áudio procedural (Web Audio API), scatter plot fenotípico interativo, comparativo de seleção de gerações e exportação de dados em CSV/JSON.

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
- [x] **Spawn de Comida Dinâmico Proporcional (Feedback Regulatório):**
  - Ajustado multiplicador de geração de alimento com curva de saturação logística quadrática (`saturation_factor`) e amortecimento populacional (`pop_ratio`).
- [x] **Especialização Ocupacional nos Clãs:**
  - Além de Alpha e Beta, membros adultos assumem papéis emergentes baseados em fenótipo e personalidade:
    - *Guardião:* Indivíduos com alta Força (`>= 58.0`) patrulham e recebem insígnia `🛡️ [GUARDIÃO]`.
    - *Coletor:* Indivíduos rápidos (`>= 56.0`) priorizam forrageamento e recebem insígnia `⚡ [COLETOR]`.
    - *Nutriz:* Fêmeas sociáveis e dóceis cuidam dos filhotes e recebem insígnia `🍼 [NUTRIZ]`.
- [x] **Persistência de Snapshot Completo em Disco:**
  - Endpoints `/api/simulation/snapshot` e `/api/simulation/restore-snapshot` permitindo salvar e restaurar ensaios científicos anteriores com integridade determinística de RNG, genealogia e crônica. Validado em `test_snapshot_api.py`.
- [ ] **Patologias & Imunidade Genética:**
  - Traço genético de resistência imunológica e probabilidade de infecção sazonal em zonas degradadas.
- [ ] **Otimizações Cinemáticas:**
  - Vetorização contínua do cálculo de forças de repulsão entre organismos para sustentar > 1.000 organismos simultâneos.

---

### 2.2 Visual, Canvas & Frontend (`frontend/`)
- [x] **Mini-Mapa / Radar Ecológico:**
  - HUD holográfico translúcido no canto inferior direito do Canvas (`renderMiniMap`) exibindo em tempo real: zonas territoriais, oásis de alimentação, espécimes vivos (Vrancos vs Predadores) e enquadramento da câmera (viewport).
- [x] **Gráficos de Dispersão Fenotípica em Tempo Real (Scatter Plot):**
  - Gráfico 2D SVG interativo no painel de evolução: Eixo X (Velocidade) vs Eixo Y (Força), linhas de quadrante (*Apex, Tanque, Ágil, Adaptativo*), hover com tooltip e clique para selecionar organismo.
- [x] **Efeitos Sonoros Biológicos Procedurais (Web Audio API):**
  - Síntese sonora procedural em tempo real em `SoundManager.ts` (sem arquivos pesados):
    - Arpeggio harmônico ascendente no nascimento (`playBirth`).
    - Impacto percussivo abafado em combates e predação (`playCombat`).
    - Acorde suave em vínculos monogâmicos (`playBond`).
    - Ressonância tríade na aclamação de clãs e líderes (`playClan`).
    - Sino eólico etéreo na transição de estações climáticas (`playSeasonChange`).
    - Botão interativo de Som/Mudo na `TopBar`.
- [ ] **Árvore Genealógica Interativa em Grafo (Filogenia Visual):**
  - Componente com visualização tipo árvore hierárquica gráfica permitindo clicar em qualquer indivíduo e rastrear linhagem.
- [ ] **Controle de Câmera Suave (Cinematic Auto-Tracking):**
  - Modo que acompanha automaticamente o habitante envolvido no evento de maior dramaticidade do ciclo.

---

### 2.3 Interface do Usuário & Análise (`MetricsPanel.tsx` & `ControlBar.tsx`)
- [x] **Exportação de Dados da Simulação:**
  - Botões dedicados no painel geral para exportar séries temporais completas em `.csv` (`exportHistoryCSV`) e ensaio integral com crônica causal em `.json` (`exportChronicleJSON`).
- [x] **Painel de Comparação de Gerações:**
  - Módulo analítico comparando a Geração 0 (Pioneiros Fundadores) com a Geração atual, quantificando a seleção natural: Δ Força, Δ Velocidade, Δ Resistência e Δ Coleta.
- [x] **Filtros Avançados na Linha do Tempo da Crônica:**
  - Filtros por espécie, tipo de acontecimento, clã, estrelas de importância e busca textual instantânea de causalidade por palavras-chave em causas e resultados históricos.

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
