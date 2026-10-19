# Regras Matemáticas e Comportamentais da Simulação — VÉSPERA

Este documento formaliza as equações diferenciais/discretas, regras estocásticas e sequências operacionais executadas em cada ciclo de simulação ($\text{tick}$).

---

## 1. Ordem Canônica de Execução por Tick

A cada ciclo temporal $t \to t+1$, o ecossistema executa rigorosamente a seguinte sequência determinística:

1. **Atualização da Indexação Espacial:** Organismos e recursos são reindexados nas células do *Spatial Hash Grid*.
2. **Percepção e Tomada de Decisão:** Cada organismo vivo consulta os recursos dentro do seu raio sensorial $r_{vis}$ e calcula as forças de aceleração (*Steering Forces*).
3. **Integração Física de Movimento:** Atualização de velocidade e posição vetorial com confinamento suave nas bordas.
4. **Metabolismo e Dedução Energética:** Cálculo e débito dos custos basal, cinético e sensorial.
5. **Ingestão de Alimento:** Verificação de proximidade física e consumo de biomassa.
6. **Mortalidade:** Coleta e eliminação de organismos com energia nula ($E \le 0$) ou idade máxima atingida ($age \ge age_{max}$).
7. **Regeneração de Recursos (Spawn):** Injeção de novos recursos estocásticos até o teto $F_{max}$.
8. **Agregação de Métricas:** Atualização de contadores de população, energia média e eventos.

---

## 2. Equações e Modelos Físico-Comportamentais

### 2.1 Cinemática e Dinâmica de Euler
Para um organismo com posição $\vec{p} = (x, y)$, velocidade $\vec{v} = (v_x, v_y)$ e força aplicada $\vec{F}$:

$$\vec{a} = \frac{\vec{F}}{m}$$

$$\vec{v}_{t+1} = \text{clamp}(\vec{v}_t + \vec{a} \cdot \Delta t, v_{max})$$

$$\vec{p}_{t+1} = \vec{p}_t + \vec{v}_{t+1} \cdot \Delta t$$

Onde $\text{clamp}(\vec{u}, v_{max})$ preserva a direção do vetor, limitando sua norma euclidiana:
$$\text{clamp}(\vec{u}, v_{max}) = \begin{cases} \vec{u}, & \text{se } \|\vec{u}\| \le v_{max} \\ \frac{\vec{u}}{\|\vec{u}\|} \cdot v_{max}, & \text{se } \|\vec{u}\| > v_{max} \end{cases}$$

### 2.2 Física de Repulsão de Borda (Soft Boundary Repulsion)
Em vez de teleportar ou rebater instantaneamente, o ambiente aplica uma força elástica repulsiva proporcional à penetração na zona de amortecimento $d_{margin}$:

Para uma borda $x=0$:
$$\text{Se } x < d_{margin} \implies F_x = k_{wall} \cdot \left(1 - \frac{x}{d_{margin}}\right)$$

Equação análoga é aplicada para $x = W - d_{margin}$, $y = 0$ e $y = H - d_{margin}$.

### 2.3 Steering Behavior (Percepção e Navegação de Reynolds)
1. **Comportamento de Perseguição (*Seek*):**
   Se houver pelo menos um recurso com distância $d = \|\vec{p}_{food} - \vec{p}\| \le r_{vis}$, o organismo seleciona o mais próximo e calcula:
   $$\vec{v}_{desejada} = \frac{\vec{p}_{food} - \vec{p}}{\|\vec{p}_{food} - \vec{p}\|} \cdot v_{max}$$
   $$\vec{F}_{steer} = \vec{v}_{desejada} - \vec{v}$$

2. **Comportamento de Vagueio (*Wander*):**
   Se nenhum alimento for detectado, o organismo mantém uma direção suave temporalmente coerente projetando um círculo imaginário à sua frente e alterando seu ângulo por uma pequena perturbação estocástica gaussiana:
   $$\theta_{t+1} = \theta_t + \Delta \theta, \quad \Delta \theta \sim \mathcal{N}(0, \sigma^2)$$

### 2.4 Balanço Metabólico
A cada ciclo, a energia $E$ varia conforme a equação:

$$E_{t+1} = E_t + E_{ingerida} - \Delta E_{gasto}$$

Onde o custo de manutenção metabólica $\Delta E_{gasto}$ é composto por:
1. **Custo Basal:** $E_{basal} = k_{basal} \cdot s^2$ (proporcional ao tamanho/massa celular).
2. **Custo Cinético:** $E_{mov} = k_{mov} \cdot s \cdot \|\vec{v}\|^2$ (gasto quadrático de deslocamento mecânico).
3. **Custo Sensorial:** $E_{vis} = k_{vis} \cdot r_{vis}$ (manutenção de receptores sensoriais).

$$\Delta E_{gasto} = E_{basal} + E_{mov} + E_{vis}$$

### 2.5 Ingestão e Renovação de Alimento
- Um recurso é consumido quando a distância euclidiana satisfaz:
  $$\|\vec{p}_{food} - \vec{p}_{org}\| \le s_{org} + r_{food}$$
- O alimento consumido transfere seu valor nutritivo $E_{food}$ integralmente para a reserva do organismo.
- A cada tick, novos recursos são gerados de acordo com a taxa $R_{spawn}$, contanto que o total de alimentos no mundo seja inferior à capacidade de suporte $F_{max}$.
