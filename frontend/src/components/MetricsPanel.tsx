import React from 'react';
import type { WorldMetrics } from '../types';
import { Users, Apple, Zap, Gauge, HeartPulse, Clock, Sparkles } from 'lucide-react';

interface MetricsPanelProps {
  metrics: WorldMetrics | null;
  history: Array<{ tick: number; pop: number; food: number; avgEnergy: number }>;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics, history }) => {
  // Gera curva SVG dos últimos 100 ticks
  const renderSparkline = () => {
    if (history.length < 2) {
      return (
        <div style={{ height: '90px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', fontSize: '11px' }}>
          Coletando dados temporais...
        </div>
      );
    }

    const svgWidth = 280;
    const svgHeight = 90;
    const padding = 8;

    const maxVal = Math.max(
      ...history.map((h) => Math.max(h.pop, h.food)),
      50
    );

    const getX = (index: number) => padding + (index / (history.length - 1)) * (svgWidth - padding * 2);
    const getY = (val: number) => svgHeight - padding - (val / maxVal) * (svgHeight - padding * 2);

    const popPath = history.reduce(
      (acc, curr, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)},${getY(curr.pop)}`,
      ''
    );

    const foodPath = history.reduce(
      (acc, curr, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)},${getY(curr.food)}`,
      ''
    );

    return (
      <div style={{ position: 'relative', marginTop: '10px' }}>
        <svg width="100%" height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ overflow: 'visible' }}>
          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={svgWidth - padding} y2={padding} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding} y1={svgHeight / 2} x2={svgWidth - padding} y2={svgHeight / 2} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding} y1={svgHeight - padding} x2={svgWidth - padding} y2={svgHeight - padding} stroke="rgba(255,255,255,0.06)" />

          {/* População (Ciano) */}
          <path d={popPath} fill="none" stroke="#38BDF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {/* Alimento (Esmeralda) */}
          <path d={foodPath} fill="none" stroke="#34D399" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="3 3" />
        </svg>

        {/* Legenda do Gráfico */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--color-text-muted)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '2px', background: '#38BDF8' }} /> População
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '2px', background: '#34D399' }} /> Alimento
          </span>
          <span>Max: {maxVal}</span>
        </div>
      </div>
    );
  };

  const energyPercentage = metrics ? Math.min(100, Math.max(0, (metrics.avg_energy / 150) * 100)) : 0;

  return (
    <aside
      className="glass-panel"
      style={{
        width: '320px',
        height: '100%',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        overflowY: 'auto',
        borderLeft: '1px solid var(--border-subtle)',
      }}
    >
      <div>
        <h2 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94A3B8' }}>
          Telemetria do Ecossistema
        </h2>
        <p style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.4)' }}>
          Monitoramento de variáveis biológicas em tempo real
        </p>
      </div>

      {/* Grid de Cards Principais */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        {/* População */}
        <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#38BDF8' }}>
            <Users size={14} /> População
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            {metrics?.population ?? 0}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            +{metrics?.total_births ?? 0} / -{metrics?.total_deaths ?? 0}
          </div>
        </div>

        {/* Recursos */}
        <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#34D399' }}>
            <Apple size={14} /> Alimentos
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            {metrics?.food_count ?? 0}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            {metrics?.total_food_consumed ?? 0} consumidos
          </div>
        </div>
      </div>

      {/* Energia Média */}
      <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#F59E0B' }}>
            <Zap size={14} /> Energia Média
          </span>
          <span style={{ fontSize: '13px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
            {metrics?.avg_energy ?? 0} kcal
          </span>
        </div>
        {/* Barra de Progresso */}
        <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', marginTop: '8px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${energyPercentage}%`,
              height: '100%',
              background: energyPercentage > 40 ? '#10B981' : energyPercentage > 20 ? '#F59E0B' : '#EF4444',
              borderRadius: '3px',
              transition: 'width 0.2s ease, background 0.2s ease',
            }}
          />
        </div>
      </div>

      {/* Dinâmica e Idade */}
      <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-muted)' }}>
              <Gauge size={13} /> Velocidade Média
            </span>
            <span style={{ fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
              {metrics?.avg_speed ?? 0} px/t
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-muted)' }}>
              <Clock size={13} /> Idade Média
            </span>
            <span style={{ fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
              {metrics?.avg_age ?? 0} ticks
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-muted)' }}>
              <Sparkles size={13} /> Idade Máxima
            </span>
            <span style={{ fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: '#A855F7' }}>
              {metrics?.max_age ?? 0} ticks
            </span>
          </div>
        </div>
      </div>

      {/* Gráfico Histórico */}
      <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)', flex: 1 }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <HeartPulse size={14} /> Curva Dinâmica Populacional
        </div>
        {renderSparkline()}
      </div>
    </aside>
  );
};
