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

## 🐛 1. Bugs Conhecidos, Riscos & Pontos de Atenção

| ID | Área | Descrição / Risco | Severidade | Status / Mitigação Atual |
|---|---|---|---|---|
| **BUG-01** | *Gênese / Demografia* | **Assimetria de Sexos na Gênese (0 a 10):** Se o RNG sortear apenas machos (ex: 7 machos e 0 fêmeas), a espécie entrará em colapso natural por incapacidade biológica de pareamento. | 🟡 Média | **Comportamento Biológico Válido.** Mitigado pelo botão "Resetar Simulação com Parâmetros", permitindo reiniciar o ecossistema ou definir contagens explícitas se desejado. |
| **BUG-02** | *Ecologia / Recursos* | **Hiperabundância Vegetal Inicial:** Se o mundo iniciar com população pioneira muito baixa (ex: 2 a 4 indivíduos) e a taxa de regeneração de comida for padrão, as frutas acumulam rapidamente até o teto (`max_food = 100`). | 🟢 Baixa | O `carrying_capacity` regional e as estações climáticas (Inverno reduz spawn para 20%) evitam crescimento infinito. Pode ser refinado ajustando o spawn proporcionalmente à biomassa ativa. |
| **BUG-03** | *Performance / Backend* | **Crescimento de Árvore Genealógica em Sessões Ultralongas:** Em simulações com mais de 50.000 ticks e centenas de gerações, o grafo genealógico em memória cresce continuamente sem descarte. | 🟡 Média | A Crônica Histórica já possui teto de 1.500 eventos e descarte FIFO, mas a genealogia retém todos os ancestrais para cálculo de *inbreeding coefficient*. Pode ser adicionado arquivamento em SQLite. |
| **BUG-04** | *Canvas / Frontend* | **Display High-DPI (Retina / 4K):** Em telas com `window.devicePixelRatio > 1`, o canvas precisa sincronizar as dimensões físicas de pixels (`width/height`) com o CSS para evitar leve blur visual ao dar zoom excessivo. | 🟢 Baixa | O viewport atual escala proporcionalmente, mas a nitidez em telas 4K pode ser elevada aplicando ajuste explícito de DPI context. |
| **BUG-05** | *WebSocket / Rede* | **Reconexão Rápida sob Queda de Conexão:** Caso o backend sofra reinício ou a aba do navegador seja minimizada pelo gerenciador de energia do sistema operacional, o socket pode desconectar silenciosamente. | 🟢 Baixa | O frontend tenta reconexão automática, mas a interface poderia exibir um badge visual mais destacado quando em modo offline temporário. |

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
