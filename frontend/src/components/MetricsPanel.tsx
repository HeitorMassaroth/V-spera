import React, { useState } from 'react';
import type { WorldMetrics, WorldEvent, CompactOrganism, FamilyInfo, NestInfo, ClanInfo } from '../types';
import { getClanName } from '../types';
import {
  Users,
  Apple,
  HeartPulse,
  Dna,
  Swords,
  Activity,
  Radio,
  ChevronRight,
  Crown,
} from 'lucide-react';

interface MetricsPanelProps {
  metrics: WorldMetrics | null;
  events: WorldEvent[];
  organisms: CompactOrganism[];
  families?: FamilyInfo[];
  nests?: NestInfo[];
  clans?: ClanInfo[];
  history: Array<{ tick: number; pop: number; food: number; avgEnergy: number }>;
  onSelectOrganism: (id: number) => void;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  events,
  organisms,
  families = [],
  nests = [],
  clans = [],
  history,
  onSelectOrganism,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'clans' | 'battles' | 'inhabitants'>('overview');
  const [inhabitantFilter, setInhabitantFilter] = useState<'all' | 'F' | 'M' | 'C'>('all');

  // Gera curva SVG dos últimos 100 ticks
  const renderSparkline = () => {
    if (history.length < 2) {
      return (
        <div
          style={{
            height: '75px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-text-muted)',
            fontSize: '11px',
          }}
        >
          Coletando dados temporais...
        </div>
      );
    }

    const svgWidth = 280;
    const svgHeight = 75;
    const padding = 8;

    const maxVal = Math.max(
      ...history.map((h) => Math.max(h.pop, h.food)),
      50
    );

    const getX = (index: number) =>
      padding + (index / (history.length - 1)) * (svgWidth - padding * 2);
    const getY = (val: number) =>
      svgHeight - padding - (val / maxVal) * (svgHeight - padding * 2);

    const popPath = history.reduce(
      (acc, curr, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)},${getY(curr.pop)}`,
      ''
    );

    const foodPath = history.reduce(
      (acc, curr, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)},${getY(curr.food)}`,
      ''
    );

    return (
      <div style={{ position: 'relative', marginTop: '6px' }}>
        <svg
          width="100%"
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ overflow: 'visible' }}
        >
          <line x1={padding} y1={padding} x2={svgWidth - padding} y2={padding} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding} y1={svgHeight / 2} x2={svgWidth - padding} y2={svgHeight / 2} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding} y1={svgHeight - padding} x2={svgWidth - padding} y2={svgHeight - padding} stroke="rgba(255,255,255,0.06)" />

          <path d={popPath} fill="none" stroke="#38BDF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <path d={foodPath} fill="none" stroke="#34D399" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="3 3" />
        </svg>

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

  const attrStats = metrics?.attr_stats;

  // Destaques da População
  const sortedByForca = [...organisms].sort((a, b) => (b.f || 0) - (a.f || 0));
  const sortedBySpeed = [...organisms].sort((a, b) => (b.v || 0) - (a.v || 0));
  const sortedByAge = [...organisms].sort((a, b) => (b.a || 0) - (a.a || 0));

  const strongest = sortedByForca[0];
  const fastest = sortedBySpeed[0];
  const oldest = sortedByAge[0];

  const filteredOrganisms = organisms.filter((o) => {
    if (inhabitantFilter === 'all') return true;
    return o.r === inhabitantFilter;
  });

  return (
    <aside
      className="glass-panel"
      style={{
        width: '340px',
        height: '100%',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        overflowY: 'hidden',
        borderLeft: '1px solid var(--border-subtle)',
      }}
    >
      {/* Header do Dashboard */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '13px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94A3B8' }}>
            Centro de Comando
          </h2>
          <span style={{ fontSize: '10px', padding: '2px 6px', background: 'rgba(56, 189, 248, 0.15)', color: '#38BDF8', borderRadius: '4px', fontWeight: 700 }}>
            TICK #{metrics?.tick ?? 0}
          </span>
        </div>
        <p style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.4)', marginTop: '2px' }}>
          Simulação de Vida, Clãs e Combates
        </p>
      </div>

      {/* Navegação de Abas do Dashboard */}
      <div
        style={{
          display: 'flex',
          background: 'rgba(11, 17, 30, 0.8)',
          borderRadius: '8px',
          padding: '3px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            flex: 1,
            padding: '6px 4px',
            fontSize: '11px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'overview' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
            color: activeTab === 'overview' ? '#38BDF8' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
          }}
        >
          <Activity size={12} /> Visão Geral
        </button>

        <button
          onClick={() => setActiveTab('clans')}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'clans' ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
            color: activeTab === 'clans' ? '#FBBF24' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <Crown size={12} /> Clãs ({clans.length})
        </button>

        <button
          onClick={() => setActiveTab('battles')}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'battles' ? 'rgba(244, 63, 94, 0.2)' : 'transparent',
            color: activeTab === 'battles' ? '#FB7185' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <Swords size={12} /> Batalhas
        </button>

        <button
          onClick={() => setActiveTab('inhabitants')}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'inhabitants' ? 'rgba(52, 211, 153, 0.2)' : 'transparent',
            color: activeTab === 'inhabitants' ? '#34D399' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <Users size={12} /> Habitantes
        </button>
      </div>

      {/* Conteúdo da Aba */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '2px' }}>
        {activeTab === 'overview' && (
          <>
            {/* População e Recursos */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#38BDF8' }}>
                  <Users size={13} /> População
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '2px', fontFamily: 'JetBrains Mono, monospace' }}>
                  {metrics?.population ?? 0}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                  +{metrics?.total_births ?? 0} / -{metrics?.total_deaths ?? 0}
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#34D399' }}>
                  <Apple size={13} /> Alimentos
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '2px', fontFamily: 'JetBrains Mono, monospace' }}>
                  {metrics?.food_count ?? 0}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                  {metrics?.total_food_consumed ?? 0} consumidos
                </div>
              </div>
            </div>

            {/* Sociedade Animal & Clãs Estratégicos */}
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                  Sociedade Animal & Clãs
                </span>
                <span style={{ fontSize: '10px', color: '#F59E0B', fontWeight: 700 }}>
                  🏰 {metrics?.established_clans_count ?? clans.filter((c) => c.stage === 'ESTABLISHED_CLAN').length} Estabelecidos
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px' }}>
                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#FCD34D' }}>Total Clãs</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#F59E0B', fontFamily: 'JetBrains Mono, monospace' }}>
                    {clans.length}
                  </div>
                </div>
                <div style={{ background: 'rgba(52, 211, 153, 0.08)', border: '1px solid rgba(52, 211, 153, 0.2)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#6EE7B7' }}>Reserva Coletiva</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#34D399', fontFamily: 'JetBrains Mono, monospace' }}>
                    {(metrics?.total_communal_food ?? clans.reduce((acc, c) => acc + (c.communal_food || 0), 0)).toFixed(0)} <span style={{ fontSize: '9px' }}>kcal</span>
                  </div>
                </div>
                <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#FCA5A5' }}>Guerras</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#EF4444', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.wars_count ?? 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Divisões e Territórios */}
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                  Divisões da População
                </span>
                <span style={{ fontSize: '10px', color: '#38BDF8', fontWeight: 600 }}>
                  {metrics?.families_count ?? 0} Clãs
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px' }}>
                <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.25)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#FDA4AF', fontWeight: 700 }}>🌸 Rosa</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#FB7185', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.females_count ?? 0}
                  </div>
                  <div style={{ fontSize: '8px', color: 'rgba(253, 164, 175, 0.7)' }}>Fêmeas</div>
                </div>

                <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#6EE7B7', fontWeight: 700 }}>🌿 Verde</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#34D399', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.males_count ?? 0}
                  </div>
                  <div style={{ fontSize: '8px', color: 'rgba(110, 231, 183, 0.7)' }}>Machos</div>
                </div>

                <div style={{ background: 'rgba(168, 85, 247, 0.1)', border: '1px solid rgba(168, 85, 247, 0.25)', padding: '6px 8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '9px', color: '#D8B4FE', fontWeight: 700 }}>💜 Roxo</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#C084FC', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.children_count ?? 0}
                  </div>
                  <div style={{ fontSize: '8px', color: 'rgba(216, 180, 254, 0.7)' }}>Filhotes</div>
                </div>
              </div>

              {/* Ninhos e Vínculos */}
              <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <div style={{ padding: '6px 8px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                  <span style={{ color: '#FCD34D' }}>🪺 Ninhos Ativos:</span>
                  <span style={{ fontWeight: 800, color: '#F59E0B', fontFamily: 'JetBrains Mono, monospace' }}>
                    {nests.length}
                  </span>
                </div>
                <div style={{ padding: '6px 8px', background: 'rgba(236, 72, 153, 0.08)', borderRadius: '6px', border: '1px solid rgba(236, 72, 153, 0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                  <span style={{ color: '#F472B6' }}>💍 Casais Vinculados:</span>
                  <span style={{ fontWeight: 800, color: '#EC4899', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.bonded_pairs_count ?? 0}
                  </span>
                </div>
              </div>

              {/* Estágios de Desenvolvimento */}
              {metrics?.stage_stats && (
                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                  <div style={{ fontSize: '9px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Estágios Etários
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px', textAlign: 'center' }}>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '3px 2px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ fontSize: '8px', color: '#CBD5E1' }}>Nascido</div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#C084FC' }}>{metrics.stage_stats.newborn}</div>
                    </div>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '3px 2px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ fontSize: '8px', color: '#CBD5E1' }}>Desenv.</div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#E879F9' }}>{metrics.stage_stats.developing}</div>
                    </div>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '3px 2px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ fontSize: '8px', color: '#CBD5E1' }}>Jovem</div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#818CF8' }}>{metrics.stage_stats.juvenile}</div>
                    </div>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '3px 2px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ fontSize: '8px', color: '#CBD5E1' }}>Indep.</div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#38BDF8' }}>{metrics.stage_stats.independent}</div>
                    </div>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '3px 2px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ fontSize: '8px', color: '#CBD5E1' }}>Adulto</div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#34D399' }}>{metrics.stage_stats.adult}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Clãs & Famílias Ativas */}
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                  Clãs Estabelecidos
                </span>
                <span style={{ fontSize: '10px', color: '#34D399', fontWeight: 700 }}>
                  {families.length} ativos
                </span>
              </div>

              {families.length === 0 ? (
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textAlign: 'center', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
                  Nenhum clã formado ainda. Machos e Fêmeas estão forrageando para fundar novos territórios.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {families.map((fam) => {
                    const famNest = nests.find((n) => n.family_id === fam.id);
                    return (
                      <div
                        key={fam.id}
                        style={{
                          background: 'rgba(15, 23, 42, 0.7)',
                          border: '1px solid rgba(52, 211, 153, 0.25)',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px',
                          fontSize: '11px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 800, color: '#6EE7B7' }}>
                            🛡️ {fam.clan_name} #{fam.id}
                          </span>
                          <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: 'rgba(52, 211, 153, 0.15)', color: '#34D399' }}>
                            {fam.home_cluster_id !== null && fam.home_cluster_id !== undefined ? `Oásis #${fam.home_cluster_id}` : 'Nômade'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-text-muted)' }}>
                          <span>
                            Patriarca: {fam.patriarch_id ? (
                              <button
                                onClick={() => onSelectOrganism(fam.patriarch_id!)}
                                style={{ background: 'none', border: 'none', color: '#34D399', fontWeight: 700, cursor: 'pointer', padding: 0 }}
                              >
                                Macho #{fam.patriarch_id}
                              </button>
                            ) : <span style={{ color: '#F87171' }}>Viúva</span>}
                          </span>
                          <span>
                            Matriarca: {fam.matriarch_id ? (
                              <button
                                onClick={() => onSelectOrganism(fam.matriarch_id!)}
                                style={{ background: 'none', border: 'none', color: '#FB7185', fontWeight: 700, cursor: 'pointer', padding: 0 }}
                              >
                                Rosa #{fam.matriarch_id}
                              </button>
                            ) : <span style={{ color: '#F87171' }}>Viúvo</span>}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '9px' }}>
                          <span style={{ color: '#D8B4FE', fontWeight: 600 }}>
                            💜 {fam.children_count} {fam.children_count === 1 ? 'filhote' : 'filhotes'}
                          </span>
                          {famNest && (
                            <span style={{ color: '#FCD34D', fontWeight: 600 }}>
                              🪺 Ninho Lvl {famNest.level} ({Math.round(famNest.food_storage)} kcal)
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Genética e Evolução */}
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Dna size={13} color="#38BDF8" /> Estatísticas Genéticas
                </span>
                <span style={{ fontSize: '10px', color: '#C084FC', fontWeight: 700 }}>
                  Gen Máx: {metrics?.max_generation ?? 0}
                </span>
              </div>

              {attrStats && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {/* Força */}
                  <div style={{ fontSize: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#E2E8F0', marginBottom: '2px' }}>
                      <span style={{ fontWeight: 600 }}>Força</span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#F59E0B' }}>
                        {attrStats.forca.avg.toFixed(1)} <span style={{ color: 'var(--color-text-muted)', fontSize: '9px' }}>[{attrStats.forca.min.toFixed(0)}-{attrStats.forca.max.toFixed(0)}]</span>
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, (attrStats.forca.avg / 30) * 100)}%`, height: '100%', background: '#F59E0B' }} />
                    </div>
                  </div>

                  {/* Velocidade */}
                  <div style={{ fontSize: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#E2E8F0', marginBottom: '2px' }}>
                      <span style={{ fontWeight: 600 }}>Velocidade</span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#38BDF8' }}>
                        {attrStats.velocidade.avg.toFixed(1)} <span style={{ color: 'var(--color-text-muted)', fontSize: '9px' }}>[{attrStats.velocidade.min.toFixed(1)}-{attrStats.velocidade.max.toFixed(1)}]</span>
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, (attrStats.velocidade.avg / 6.0) * 100)}%`, height: '100%', background: '#38BDF8' }} />
                    </div>
                  </div>

                  {/* Resistência */}
                  <div style={{ fontSize: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#E2E8F0', marginBottom: '2px' }}>
                      <span style={{ fontWeight: 600 }}>Resistência</span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#34D399' }}>
                        {attrStats.resistencia.avg.toFixed(1)} <span style={{ color: 'var(--color-text-muted)', fontSize: '9px' }}>[{attrStats.resistencia.min.toFixed(0)}-{attrStats.resistencia.max.toFixed(0)}]</span>
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, (attrStats.resistencia.avg / 30) * 100)}%`, height: '100%', background: '#34D399' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Curva Histórica */}
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <HeartPulse size={13} /> Dinâmica Populacional
              </div>
              {renderSparkline()}
            </div>
          </>
        )}

        {/* ABA DE CLÃS E ESTRATÉGIA COLETIVA */}
        {activeTab === 'clans' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Comunidades & Clãs ({clans.length})
              </span>
              <span style={{ fontSize: '10px', color: '#38BDF8' }}>
                {clans.filter((c) => c.stage === 'ESTABLISHED_CLAN').length} Estabelecidos
              </span>
            </div>

            {clans.length === 0 ? (
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px dashed rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  padding: '24px 16px',
                  textAlign: 'center',
                  color: 'var(--color-text-muted)',
                  fontSize: '11px',
                  lineHeight: '1.6',
                }}
              >
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>🏰</div>
                <div style={{ fontWeight: 700, color: '#F8FAFC', marginBottom: '4px' }}>
                  Nenhum clã formado ainda
                </div>
                <div>
                  Clãs emergem espontaneamente quando 3 ou mais famílias próximas cooperam, compartilham alimentos e reconhecem vantagens na defesa coletiva.
                </div>
              </div>
            ) : (
              clans.map((clan) => {
                const isEstablished = clan.stage === 'ESTABLISHED_CLAN';
                const relations = clan.relations || clan.diplomacy || {};
                const isAtWar = Object.values(relations).includes('WAR');

                const getStageBadgeInfo = (st: string) => {
                  switch (st) {
                    case 'ESTABLISHED_CLAN':
                      return { label: 'Clã Estabelecido', color: '#FBBF24', bg: 'rgba(245, 158, 11, 0.15)' };
                    case 'RECURRENT_COOP':
                      return { label: 'Coop. Recorrente', color: '#C084FC', bg: 'rgba(192, 132, 252, 0.15)' };
                    case 'OCCASIONAL_COOP':
                      return { label: 'Coop. Ocasional', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.15)' };
                    case 'INDEPENDENT':
                    default:
                      return { label: 'Famílias Independentes', color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.15)' };
                  }
                };

                const stageInfo = getStageBadgeInfo(clan.stage);

                return (
                  <div
                    key={clan.id}
                    style={{
                      background: 'rgba(15, 23, 42, 0.75)',
                      border: isAtWar
                        ? '1px solid rgba(239, 68, 68, 0.5)'
                        : isEstablished
                        ? '1px solid rgba(245, 158, 11, 0.35)'
                        : '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '10px',
                      padding: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                    }}
                  >
                    {/* Header do Clã */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>
                            🏰 {clan.name}
                          </span>
                          <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                            #{clan.id}
                          </span>
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          {clan.family_ids.length} famílias &bull; {clan.member_organism_ids ? clan.member_organism_ids.length : clan.family_ids.length * 3} habitantes
                        </div>
                      </div>

                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 700,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          background: isAtWar ? 'rgba(239, 68, 68, 0.2)' : stageInfo.bg,
                          color: isAtWar ? '#F87171' : stageInfo.color,
                          border: `1px solid ${isAtWar ? 'rgba(239, 68, 68, 0.4)' : stageInfo.color + '40'}`,
                        }}
                      >
                        {isAtWar ? '⚔️ EM GUERRA' : stageInfo.label}
                      </span>
                    </div>

                    {/* Liderança: Alpha & Beta */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      {/* Card Alpha */}
                      <div
                        onClick={() => clan.alpha_id && onSelectOrganism(clan.alpha_id)}
                        style={{
                          background: 'rgba(245, 158, 11, 0.08)',
                          border: '1px solid rgba(245, 158, 11, 0.25)',
                          borderRadius: '6px',
                          padding: '6px 8px',
                          cursor: clan.alpha_id ? 'pointer' : 'default',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '10px', fontWeight: 800, color: '#FCD34D' }}>
                            👑 ALPHA
                          </span>
                          {clan.alpha_score !== undefined && (
                            <span style={{ fontSize: '9px', fontWeight: 700, color: '#FBBF24', fontFamily: 'JetBrains Mono, monospace' }}>
                              {clan.alpha_score.toFixed(1)}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC', marginTop: '2px' }}>
                          {clan.alpha_id ? `Animal #${clan.alpha_id}` : 'Vago (Sem líder)'}
                        </div>
                        <div style={{ fontSize: '8px', color: 'rgba(255, 255, 255, 0.5)' }}>
                          {clan.alpha_id ? 'Líder Supremo' : 'Aguardando elegível'}
                        </div>
                      </div>

                      {/* Card Beta */}
                      <div
                        onClick={() => clan.beta_id && onSelectOrganism(clan.beta_id)}
                        style={{
                          background: 'rgba(56, 189, 248, 0.08)',
                          border: '1px solid rgba(56, 189, 248, 0.25)',
                          borderRadius: '6px',
                          padding: '6px 8px',
                          cursor: clan.beta_id ? 'pointer' : 'default',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '10px', fontWeight: 800, color: '#7DD3FC' }}>
                            ⭐ BETA
                          </span>
                          {clan.beta_score !== undefined && (
                            <span style={{ fontSize: '9px', fontWeight: 700, color: '#38BDF8', fontFamily: 'JetBrains Mono, monospace' }}>
                              {clan.beta_score.toFixed(1)}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC', marginTop: '2px' }}>
                          {clan.beta_id ? `Animal #${clan.beta_id}` : 'Vago'}
                        </div>
                        <div style={{ fontSize: '8px', color: 'rgba(255, 255, 255, 0.5)' }}>
                          {clan.beta_id ? 'Sub-líder e Sucessor' : 'Aguardando elegível'}
                        </div>
                      </div>
                    </div>

                    {/* Reserva Comunal de Alimento */}
                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '8px 10px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                        <span style={{ color: '#94A3B8', fontWeight: 600 }}>🥩 Reserva Coletiva</span>
                        <span style={{ color: '#34D399', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace' }}>
                          {clan.communal_food.toFixed(1)} kcal
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '5px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', marginTop: '5px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Math.min(100, (clan.communal_food / 150) * 100)}%`,
                            height: '100%',
                            background: '#10B981',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: 'var(--color-text-muted)', marginTop: '3px' }}>
                        <span>Contribuição ativa</span>
                        <span>Auto-sustento & Defesa</span>
                      </div>
                    </div>

                    {/* Fila de Prioridades Coletivas */}
                    {clan.priorities && clan.priorities.length > 0 && (
                      <div>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '4px' }}>
                          Prioridades do Alpha
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {clan.priorities.slice(0, 3).map((p, idx) => (
                            <div
                              key={idx}
                              style={{
                                background: idx === 0 ? 'rgba(245, 158, 11, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                                border: idx === 0 ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                fontSize: '10px',
                              }}
                            >
                              <span style={{ color: idx === 0 ? '#FDE68A' : '#CBD5E1', fontWeight: idx === 0 ? 700 : 500 }}>
                                #{idx + 1} {p.description}
                              </span>
                              <span style={{ fontSize: '8px', padding: '1px 4px', borderRadius: '3px', background: 'rgba(0,0,0,0.3)', color: '#94A3B8' }}>
                                P{p.priority_level ?? p.urgency ?? 1}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Relações Diplomáticas */}
                    {Object.keys(relations).length > 0 && (
                      <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '6px' }}>
                        <div style={{ fontSize: '9px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '4px' }}>
                          Diplomacia com outros Clãs
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {Object.entries(relations).map(([targetClanId, rel]) => {
                            let relColor = '#94A3B8';
                            let relIcon = '🤝';
                            if (rel === 'WAR') {
                              relColor = '#EF4444';
                              relIcon = '⚔️';
                            } else if (rel === 'HOSTILE') {
                              relColor = '#F97316';
                              relIcon = '⚡';
                            } else if (rel === 'COMPETITION') {
                              relColor = '#FBBF24';
                              relIcon = '🏹';
                            } else if (rel === 'TRUCE') {
                              relColor = '#34D399';
                              relIcon = '🕊️';
                            }
                            return (
                              <span
                                key={targetClanId}
                                style={{
                                  fontSize: '9px',
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  background: `${relColor}18`,
                                  color: relColor,
                                  border: `1px solid ${relColor}40`,
                                  fontWeight: 600,
                                }}
                              >
                                {relIcon} Clã #{targetClanId}: {rel}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Histórico Recente do Clã */}
                    {clan.history_log && clan.history_log.length > 0 && (
                      <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '6px' }}>
                        <div style={{ fontSize: '9px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '3px' }}>
                          Memória Histórica
                        </div>
                        <div style={{ maxHeight: '60px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          {clan.history_log.slice(-3).reverse().map((log, lIdx) => {
                            const text = typeof log === 'string' ? log : log.desc || log.type || 'Evento';
                            return (
                              <div key={lIdx} style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>
                                &bull; {text}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'battles' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase' }}>
              <Radio size={13} color="#FB7185" /> Feed de Acontecimentos do Ecossistema
            </div>

            {events.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 12px', color: 'var(--color-text-muted)', fontSize: '11px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                Aguardando confrontos territoriais ou eventos familiares...
              </div>
            ) : (
              [...events].reverse().slice(0, 25).map((ev, idx) => {
                let badgeColor = '#38BDF8';
                let icon = '⚡';
                let title = 'Evento';
                let desc = '';

                if (ev.type === 'combat') {
                  badgeColor = '#F43F5E';
                  icon = '⚔️';
                  title = 'Combate Territorial';
                  desc = `${ev.macho_name} atacou ${ev.target_name} (-${ev.damage} HP)`;
                } else if (ev.type === 'flee') {
                  badgeColor = '#F59E0B';
                  icon = '💨';
                  title = 'Fuga em Pânico';
                  desc = `${ev.organism_name} debandou após ser ferido por ${ev.macho_name}!`;
                } else if (ev.type === 'care') {
                  badgeColor = '#10B981';
                  icon = '🍼';
                  title = 'Cuidado Parental';
                  desc = `${ev.parent_name} alimentou ${ev.child_name} no ninho (+12 kcal)`;
                } else if (ev.type === 'family_founded') {
                  badgeColor = '#38BDF8';
                  icon = '🏰';
                  title = 'Clã Fundado';
                  desc = `${ev.male_name} e ${ev.female_name} estabeleceram o ${ev.clan_name}`;
                } else if (ev.type === 'birth') {
                  badgeColor = '#C084FC';
                  icon = '🐣';
                  title = 'Novo Nascimento';
                  desc = `${ev.child_name} nasceu no ${ev.clan_name} (Gen ${ev.gen})`;
                } else if (ev.type === 'maturation') {
                  badgeColor = '#34D399';
                  icon = '🌟';
                  title = 'Maturação';
                  desc = `${ev.name} amadureceu e tornou-se adulto!`;
                } else if (ev.type === 'pair_bonded') {
                  badgeColor = '#EC4899';
                  icon = '💍';
                  title = 'Vínculo Vitalício';
                  desc = `${ev.male_name} e ${ev.female_name} formaram vínculo monogâmico exclusivo!`;
                } else if (ev.type === 'nest_created') {
                  badgeColor = '#F59E0B';
                  icon = '🪺';
                  title = 'Ninho Construído';
                  desc = `Ninho estabelecido pelo clã (${ev.x?.toFixed(0)}, ${ev.y?.toFixed(0)})`;
                } else if (ev.type === 'partner_lost') {
                  badgeColor = '#94A3B8';
                  icon = '🥀';
                  title = 'Luto / Perda de Parceiro';
                  desc = `${ev.organism_name || ev.survivor_name} chora a perda do seu parceiro!`;
                } else if (ev.type === 'predation_attempt') {
                  badgeColor = '#EF4444';
                  icon = '🐺';
                  title = 'Tentativa de Predação';
                  desc = `${ev.predator_name} tentou predar o filhote ${ev.pup_name || ev.child_name}!`;
                } else if (ev.type === 'predation_kill') {
                  badgeColor = '#991B1B';
                  icon = '💀';
                  title = 'Predação Consumada';
                  desc = `${ev.predator_name} predou o filhote ${ev.pup_name || ev.child_name} (-${ev.damage} HP)!`;
                } else if (ev.type === 'mother_defense') {
                  badgeColor = '#059669';
                  icon = '🛡️';
                  title = 'Defesa Parental';
                  desc = `${ev.mother_name || 'Mãe'} interceptou o predador ${ev.predator_name} para proteger a prole!`;
                } else if (ev.type === 'orphan_adopted') {
                  badgeColor = '#8B5CF6';
                  icon = '🤝';
                  title = 'Filhote Adotado';
                  desc = `Filhote órfão acolhido por novo protetor familiar`;
                } else if (ev.type === 'clan_formed') {
                  badgeColor = '#A78BFA';
                  icon = '🏰';
                  title = 'Clã Formado';
                  desc = ev.message || 'Novo clã estabelecido por cooperação de famílias!';
                } else if (ev.type === 'alpha_elected') {
                  badgeColor = '#FBBF24';
                  icon = '👑';
                  title = 'Eleição de Alpha';
                  desc = ev.message || 'Novo líder supremo do clã assumiu o posto!';
                } else if (ev.type === 'beta_elected') {
                  badgeColor = '#93C5FD';
                  icon = '⭐';
                  title = 'Eleição de Beta';
                  desc = ev.message || 'Novo sub-líder do clã nomeado!';
                } else if (ev.type === 'clan_war_declared') {
                  badgeColor = '#EF4444';
                  icon = '⚔️';
                  title = 'Guerra Declarada';
                  desc = ev.message || 'Dois clãs entraram em conflito por território!';
                } else if (ev.type === 'clan_truce_agreed') {
                  badgeColor = '#34D399';
                  icon = '🕊️';
                  title = 'Trégua Firmada';
                  desc = ev.message || 'Clãs exaustos concordaram em cessar as hostilidades!';
                } else if (ev.type === 'family_expelled') {
                  badgeColor = '#FB923C';
                  icon = '🚫';
                  title = 'Família Expulsa';
                  desc = ev.message || 'Família banida do clã por desarmonia ou escassez!';
                }

                return (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(15, 23, 42, 0.75)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      borderRadius: '8px',
                      padding: '8px 10px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '3px',
                      fontSize: '11px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 800, color: badgeColor, display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px' }}>
                        <span>{icon}</span> {title}
                      </span>
                      <span style={{ fontSize: '9px', color: 'var(--color-text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
                        t={ev.tick}
                      </span>
                    </div>
                    <div style={{ color: '#F1F5F9', fontWeight: 500 }}>
                      {desc}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'inhabitants' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Cards de Destaque */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', color: '#94A3B8' }}>
                Líderes & Destaques
              </span>

              {strongest && (
                <div
                  onClick={() => onSelectOrganism(strongest.id)}
                  style={{
                    background: 'rgba(245, 158, 11, 0.12)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '10px', color: '#F59E0B', fontWeight: 800 }}>👑 Mais Forte da População</div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>{strongest.nm}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: '#F59E0B', fontFamily: 'JetBrains Mono, monospace' }}>
                      {strongest.f?.toFixed(1)} Força
                    </div>
                    <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>{getClanName(strongest.fam)}</div>
                  </div>
                </div>
              )}

              {fastest && (
                <div
                  onClick={() => onSelectOrganism(fastest.id)}
                  style={{
                    background: 'rgba(56, 189, 248, 0.12)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '10px', color: '#38BDF8', fontWeight: 800 }}>⚡ Mais Veloz da População</div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>{fastest.nm}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: '#38BDF8', fontFamily: 'JetBrains Mono, monospace' }}>
                      {fastest.v?.toFixed(1)} px/t
                    </div>
                    <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>{getClanName(fastest.fam)}</div>
                  </div>
                </div>
              )}

              {oldest && (
                <div
                  onClick={() => onSelectOrganism(oldest.id)}
                  style={{
                    background: 'rgba(168, 85, 247, 0.12)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '10px', color: '#C084FC', fontWeight: 800 }}>⏳ Habitante Ancião</div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>{oldest.nm}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: '#C084FC', fontFamily: 'JetBrains Mono, monospace' }}>
                      {oldest.a} ticks
                    </div>
                    <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Gen {oldest.gen}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Filtros de Habitantes */}
            <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
              {(['all', 'M', 'F', 'C'] as const).map((role) => (
                <button
                  key={role}
                  onClick={() => setInhabitantFilter(role)}
                  style={{
                    flex: 1,
                    padding: '4px',
                    fontSize: '10px',
                    fontWeight: 700,
                    borderRadius: '5px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background: inhabitantFilter === role ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                    color: inhabitantFilter === role ? '#38BDF8' : 'var(--color-text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  {role === 'all' ? 'Todos' : role === 'M' ? 'Machos' : role === 'F' ? 'Fêmeas' : 'Filhotes'}
                </button>
              ))}
            </div>

            {/* Lista Scrollável de Habitantes */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '280px', overflowY: 'auto' }}>
              {filteredOrganisms.map((org) => {
                const clan = getClanName(org.fam);
                const roleDot = org.r === 'M' ? '#34D399' : org.r === 'F' ? '#FB7185' : '#C084FC';
                    const stageLabel = org.st === 'N' ? '🐣 Recém-nascido' : org.st === 'D' ? '🌱 Em desenv.' : org.st === 'J' ? '🐾 Jovem' : org.st === 'I' ? '🏹 Indep.' : '👑 Adulto';
                    const hasCarriedFood = org.cf && org.cf > 0.5;
                    return (
                      <div
                        key={org.id}
                        onClick={() => onSelectOrganism(org.id)}
                        style={{
                          background: 'rgba(15, 23, 42, 0.6)',
                          border: '1px solid rgba(255, 255, 255, 0.05)',
                          padding: '8px 10px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: roleDot, display: 'inline-block' }} />
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                              <span style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC' }}>{org.nm}</span>
                              <span style={{ fontSize: '8px', padding: '0px 3px', borderRadius: '3px', background: 'rgba(255, 255, 255, 0.06)', color: '#CBD5E1' }}>
                                {stageLabel}
                              </span>
                              {hasCarriedFood && (
                                <span style={{ fontSize: '8px', color: '#FCD34D', fontWeight: 700 }}>
                                  🌾 {Math.round(org.cf!)}
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>
                              {clan} &bull; HP: {Math.round(org.s)} &bull; {org.act || 'ativo'}
                            </div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38BDF8', fontSize: '11px' }}>
                          <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>#{org.id}</span>
                          <ChevronRight size={13} />
                        </div>
                      </div>
                    );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
