import React, { useState, useEffect, useCallback } from 'react';
import type {
  WorldMetrics,
  WorldEvent,
  CompactOrganism,
  FamilyInfo,
  NestInfo,
  ClanInfo,
  TerritoryZoneInfo,
  SeasonInfo,
  EcologyMetrics,
  ChronicleEvent,
  ChronicleTimelineResponse,
  ChronicleEventDetailResponse,
} from '../types';
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
  Shield,
  BookOpen,
  Search,
  Clock,
  RefreshCw,
  ArrowRight,
  CornerDownRight,
  X,
  Download,
  FileSpreadsheet,
  FileJson,
  TrendingUp,
  BarChart2,
} from 'lucide-react';

interface MetricsPanelProps {
  metrics: WorldMetrics | null;
  season?: SeasonInfo | null;
  ecology?: EcologyMetrics | null;
  events: WorldEvent[];
  organisms: CompactOrganism[];
  families?: FamilyInfo[];
  nests?: NestInfo[];
  clans?: ClanInfo[];
  territories?: TerritoryZoneInfo[];
  history: Array<{ tick: number; pop: number; food: number; avgEnergy: number }>;
  onSelectOrganism: (id: number) => void;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  season,
  ecology,
  events,
  organisms,
  families = [],
  nests = [],
  clans = [],
  territories = [],
  history,
  onSelectOrganism,
}) => {
  const currentSeason = season ?? metrics?.season;
  const currentEcology = ecology ?? metrics?.ecology;
  const [activeTab, setActiveTab] = useState<'overview' | 'territories' | 'clans' | 'chronicle' | 'evolution' | 'battles' | 'inhabitants'>('overview');
  const [inhabitantFilter, setInhabitantFilter] = useState<'all' | 'V' | 'P' | 'F' | 'M' | 'C'>('all');

  // Estados da Crônica Histórica Centralizada
  const [chronicleEvents, setChronicleEvents] = useState<ChronicleEvent[]>([]);
  const [chronicleTotal, setChronicleTotal] = useState<number>(0);
  const [chronicleSpecies, setChronicleSpecies] = useState<string>('all');
  const [chronicleCategory, setChronicleCategory] = useState<string>('all');
  const [chronicleClan, setChronicleClan] = useState<string>('all');
  const [chronicleImportance, setChronicleImportance] = useState<number>(1);
  const [chronicleSearch, setChronicleSearch] = useState<string>('');
  const [chronicleLoading, setChronicleLoading] = useState<boolean>(false);
  const [selectedChronicleEvent, setSelectedChronicleEvent] = useState<ChronicleEvent | null>(null);
  const [relatedChronicleEvents, setRelatedChronicleEvents] = useState<ChronicleEvent[]>([]);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  const fetchChronicle = useCallback(async () => {
    setChronicleLoading(true);
    try {
      const params = new URLSearchParams();
      if (chronicleSpecies !== 'all') params.append('species', chronicleSpecies);
      if (chronicleCategory !== 'all') params.append('event_type', chronicleCategory);
      if (chronicleClan !== 'all') params.append('clan_id', chronicleClan);
      if (chronicleImportance > 1) params.append('min_importance', chronicleImportance.toString());
      if (chronicleSearch.trim()) params.append('search', chronicleSearch.trim());
      params.append('limit', '80');

      const res = await fetch(`/api/simulation/chronicle?${params.toString()}`);
      if (res.ok) {
        const json: ChronicleTimelineResponse = await res.json();
        setChronicleEvents(json.events || []);
        setChronicleTotal(json.total || 0);
      }
    } catch (e) {
      console.error('Falha ao carregar crônica histórica:', e);
    } finally {
      setChronicleLoading(false);
    }
  }, [chronicleSpecies, chronicleCategory, chronicleClan, chronicleImportance, chronicleSearch]);

  useEffect(() => {
    if (activeTab === 'chronicle') {
      fetchChronicle();
    }
  }, [activeTab, fetchChronicle]);

  const handleInspectChronicleEvent = async (event: ChronicleEvent) => {
    setSelectedChronicleEvent(event);
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/simulation/chronicle/${event.id}`);
      if (res.ok) {
        const json: ChronicleEventDetailResponse = await res.json();
        setRelatedChronicleEvents(json.related_events || []);
      }
    } catch (e) {
      console.error('Falha ao carregar detalhes do evento:', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const [hoveredScatterOrg, setHoveredScatterOrg] = useState<CompactOrganism | null>(null);

  // Exportação de Dados: Séries temporais em CSV
  const exportHistoryCSV = () => {
    if (!history || history.length === 0) return;
    const headers = ['tick', 'populacao', 'alimentos', 'energia_media'];
    const rows = history.map((h) => [h.tick, h.pop, h.food, h.avgEnergy.toFixed(2)]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `vespera_telemetria_t${metrics?.tick ?? 0}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Exportação de Dados: Crônica e Telemetria em JSON
  const exportChronicleJSON = async () => {
    try {
      const res = await fetch('/api/simulation/chronicle?limit=250');
      const dataToExport: Record<string, unknown> = {
        tick: metrics?.tick ?? 0,
        exported_at: new Date().toISOString(),
        metrics: metrics,
        ecology: currentEcology,
        season: currentSeason,
        history: history,
      };
      if (res.ok) {
        const json = await res.json();
        dataToExport.chronicle = json;
      }
      const jsonContent = JSON.stringify(dataToExport, null, 2);
      const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `vespera_ensaio_completo_t${metrics?.tick ?? 0}.json`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Falha ao exportar JSON:', e);
    }
  };

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
    if (inhabitantFilter === 'V') return o.sp === 'V';
    if (inhabitantFilter === 'P') return o.sp !== 'V';
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
          onClick={() => setActiveTab('territories')}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'territories' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
            color: activeTab === 'territories' ? '#34D399' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <Shield size={12} /> Zonas ({territories.length})
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
          onClick={() => {
            setActiveTab('chronicle');
            setSelectedChronicleEvent(null);
          }}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'chronicle' ? 'rgba(234, 179, 8, 0.2)' : 'transparent',
            color: activeTab === 'chronicle' ? '#FBBF24' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <BookOpen size={12} /> Crônica
        </button>

        <button
          onClick={() => setActiveTab('evolution')}
          style={{
            flex: 1,
            padding: '6px 3px',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'evolution' ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
            color: activeTab === 'evolution' ? '#C084FC' : 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}
        >
          <Dna size={12} /> Evolução
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

            {/* 🌿 Ciclos Ambientais & Equilíbrio Ecológico */}
            {currentSeason && currentEcology && (
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)',
                  padding: '12px',
                  borderRadius: '8px',
                  border: `1px solid ${
                    currentSeason.season === 'SPRING'
                      ? 'rgba(16, 185, 129, 0.35)'
                      : currentSeason.season === 'SUMMER'
                      ? 'rgba(245, 158, 11, 0.35)'
                      : currentSeason.season === 'AUTUMN'
                      ? 'rgba(234, 88, 12, 0.35)'
                      : 'rgba(56, 189, 248, 0.35)'
                  }`,
                  boxShadow: '0 4px 15px rgba(0,0,0,0.25)',
                }}
              >
                {/* Header da Estação e Ano */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '15px' }}>{currentSeason.season_icon}</span>
                    <span style={{ fontSize: '12px', fontWeight: 800, color: '#F8FAFC' }}>
                      {currentSeason.season_name} · Ano {currentSeason.year}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: 'rgba(255, 255, 255, 0.08)',
                        fontFamily: 'JetBrains Mono, monospace',
                        color: '#38BDF8',
                      }}
                    >
                      {currentSeason.temperature.toFixed(1)}°C
                    </span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                    {Math.round(currentSeason.season_progress * 100)}% da estação
                  </div>
                </div>

                {/* Barra de Progresso Sazonal */}
                <div style={{ width: '100%', height: '4px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '2px', overflow: 'hidden', marginBottom: '10px' }}>
                  <div
                    style={{
                      width: `${Math.round(currentSeason.season_progress * 100)}%`,
                      height: '100%',
                      background:
                        currentSeason.season === 'SPRING'
                          ? 'linear-gradient(90deg, #10B981, #34D399)'
                          : currentSeason.season === 'SUMMER'
                          ? 'linear-gradient(90deg, #F59E0B, #FBBF24)'
                          : currentSeason.season === 'AUTUMN'
                          ? 'linear-gradient(90deg, #EA580C, #FB923C)'
                          : 'linear-gradient(90deg, #0284C7, #38BDF8)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>

                {/* Modificadores Climáticos Sazonais */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '10px' }}>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '5px 6px', borderRadius: '5px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <div style={{ fontSize: '8px', color: '#94A3B8', textTransform: 'uppercase' }}>Regeneração</div>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: currentSeason.food_spawn_multiplier >= 1.0 ? '#34D399' : '#F87171', fontFamily: 'JetBrains Mono, monospace' }}>
                      {currentSeason.food_spawn_multiplier.toFixed(2)}x
                    </div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '5px 6px', borderRadius: '5px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <div style={{ fontSize: '8px', color: '#94A3B8', textTransform: 'uppercase' }}>Metabolismo</div>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: currentSeason.metabolic_cost_multiplier <= 1.0 ? '#34D399' : '#FBBF24', fontFamily: 'JetBrains Mono, monospace' }}>
                      {currentSeason.metabolic_cost_multiplier.toFixed(2)}x
                    </div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '5px 6px', borderRadius: '5px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <div style={{ fontSize: '8px', color: '#94A3B8', textTransform: 'uppercase' }}>Limiar Reprod.</div>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: currentSeason.reproduction_cost_multiplier <= 1.0 ? '#34D399' : '#F87171', fontFamily: 'JetBrains Mono, monospace' }}>
                      {currentSeason.reproduction_cost_multiplier.toFixed(2)}x
                    </div>
                  </div>
                </div>

                {/* Balanço de Biomassa & Capacidade de Suporte */}
                <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '8px 10px', borderRadius: '6px', marginBottom: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', marginBottom: '4px' }}>
                    <span style={{ color: '#CBD5E1', fontWeight: 700 }}>Capacidade de Suporte</span>
                    <span
                      style={{
                        fontSize: '9px',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        background: currentEcology.is_overpopulated ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: currentEcology.is_overpopulated ? '#EF4444' : '#10B981',
                        fontWeight: 800,
                      }}
                    >
                      {currentEcology.is_overpopulated ? '⚠️ SOBRECARGA' : 'EQUILIBRADA'} ({Math.round(currentEcology.carrying_capacity_ratio * 100)}%)
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.min(100, Math.round(currentEcology.carrying_capacity_ratio * 100))}%`,
                        height: '100%',
                        background: currentEcology.is_overpopulated ? '#EF4444' : '#10B981',
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#94A3B8', marginTop: '4px' }}>
                    <span>Pop: {metrics?.population ?? 0} hab.</span>
                    <span>Biomassa Total: {currentEcology.total_biomass} kcal</span>
                    <span>Capacidade: {currentEcology.carrying_capacity} hab.</span>
                  </div>
                </div>

                {/* Fluxo de Biomassa: Consumo vs. Regeneração */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '8px' }}>
                  <div style={{ background: 'rgba(52, 211, 153, 0.08)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(52, 211, 153, 0.2)' }}>
                    <div style={{ fontSize: '8px', color: '#6EE7B7', textTransform: 'uppercase' }}>Regeneração</div>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#34D399', fontFamily: 'JetBrains Mono, monospace' }}>
                      +{currentEcology.regeneration_rate} <span style={{ fontSize: '8px' }}>kcal/t</span>
                    </div>
                  </div>
                  <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                    <div style={{ fontSize: '8px', color: '#FCA5A5', textTransform: 'uppercase' }}>Consumo</div>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#F87171', fontFamily: 'JetBrains Mono, monospace' }}>
                      -{currentEcology.consumption_rate} <span style={{ fontSize: '8px' }}>kcal/t</span>
                    </div>
                  </div>
                </div>

                {/* Balanço Demográfico Sazonal e Saldo Líquido */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', paddingTop: '4px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                  <span style={{ color: '#94A3B8' }}>
                    Saldo Líquido:{' '}
                    <strong style={{ color: currentEcology.biomass_balance >= 0 ? '#34D399' : '#F87171' }}>
                      {currentEcology.biomass_balance > 0 ? '+' : ''}{currentEcology.biomass_balance} kcal/t
                    </strong>
                  </span>
                  <span style={{ color: '#94A3B8' }}>
                    Regiões Críticas:{' '}
                    <strong style={{ color: currentEcology.critical_regions_count > 0 ? '#FBBF24' : '#34D399' }}>
                      {currentEcology.critical_regions_count}
                    </strong>
                  </span>
                </div>
              </div>
            )}

            {/* Coexistência Ecológica das Raças: Vrancos vs Predadores */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.7) 100%)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: '#FDE047', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  ⚔️ Raças: Vrancos vs Predadores
                </span>
                <span style={{ fontSize: '9px', color: '#94A3B8' }}>
                  Balanço Populacional
                </span>
              </div>

              {/* Barra comparativa de população */}
              {(() => {
                const vrancosCount = metrics?.vrancos_count ?? organisms.filter((o) => o.sp === 'V').length;
                const predatorsCount = metrics?.predators_count ?? organisms.filter((o) => o.sp !== 'V').length;
                const totalRaces = Math.max(1, vrancosCount + predatorsCount);
                const vrancosPct = Math.round((vrancosCount / totalRaces) * 100);
                const predatorsPct = 100 - vrancosPct;

                return (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '4px' }}>
                      <span style={{ color: '#F59E0B' }}>⚡ Vrancos: {vrancosCount} ({vrancosPct}%)</span>
                      <span style={{ color: '#10B981' }}>🐺 Predadores: {predatorsCount} ({predatorsPct}%)</span>
                    </div>
                    <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden', display: 'flex' }}>
                      <div style={{ width: `${vrancosPct}%`, background: 'linear-gradient(90deg, #F59E0B, #FBBF24)', transition: 'width 0.3s ease' }} />
                      <div style={{ width: `${predatorsPct}%`, background: 'linear-gradient(90deg, #34D399, #10B981)', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>
                );
              })()}

              {/* Indicadores Ecológicos de Confronto e Defesa */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginTop: '10px' }}>
                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '8px', color: '#FCD34D', textTransform: 'uppercase' }}>Grupo Médio</div>
                  <div style={{ fontSize: '13px', fontWeight: 800, color: '#FDE047', fontFamily: 'JetBrains Mono, monospace' }}>
                    {(metrics?.vranco_avg_group_size ?? 1.0).toFixed(1)}
                  </div>
                  <div style={{ fontSize: '7px', color: '#94A3B8' }}>Vrancos/Bando</div>
                </div>

                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '8px', color: '#FCD34D', textTransform: 'uppercase' }}>🛡️ Mobbing</div>
                  <div style={{ fontSize: '13px', fontWeight: 800, color: '#FBBF24', fontFamily: 'JetBrains Mono, monospace' }}>
                    {metrics?.collective_defenses_count ?? 0}
                  </div>
                  <div style={{ fontSize: '7px', color: '#94A3B8' }}>Defesas Coletivas</div>
                </div>

                <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.2)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '8px', color: '#7DD3FC', textTransform: 'uppercase' }}>Periferia</div>
                  <div style={{ fontSize: '13px', fontWeight: 800, color: '#38BDF8', fontFamily: 'JetBrains Mono, monospace' }}>
                    {(metrics?.vrancos_periphery_pct ?? 0).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '7px', color: '#94A3B8' }}>Vrancos nas Bordas</div>
                </div>
              </div>

              {/* Estatísticas de Caça e Predação */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', marginTop: '6px' }}>
                <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '6px 8px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '8px', color: '#FCA5A5' }}>Predação (Kills)</div>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#EF4444', fontFamily: 'JetBrains Mono, monospace' }}>
                      {metrics?.predation_kills ?? 0} <span style={{ fontSize: '8px', color: '#94A3B8' }}>({((metrics?.hunting_success_rate ?? 0) * 100).toFixed(0)}%)</span>
                    </div>
                  </div>
                  <span style={{ fontSize: '14px' }}>🐺</span>
                </div>

                <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '6px 8px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '8px', color: '#6EE7B7' }}>Fugas & Vitórias</div>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#34D399', fontFamily: 'JetBrains Mono, monospace' }}>
                      {metrics?.flee_count ?? 0} <span style={{ fontSize: '8px', color: '#FDE047' }}>(⚡{metrics?.predators_defeated ?? 0})</span>
                    </div>
                  </div>
                  <span style={{ fontSize: '14px' }}>💨</span>
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

            {/* Exportação de Dados Científicos */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.85) 100%)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Download size={13} /> Exportação de Dados
                </div>
                <span style={{ fontSize: '9px', color: '#94A3B8' }}>Telemetria & Crônica</span>
              </div>
              <p style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.6)', lineHeight: '1.4' }}>
                Baixe séries temporais e crônicas causais para análise em R, Python (Pandas) ou planilhas.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <button
                  onClick={exportHistoryCSV}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    padding: '6px 8px',
                    fontSize: '10px',
                    fontWeight: 700,
                    borderRadius: '6px',
                    border: '1px solid rgba(52, 211, 153, 0.35)',
                    background: 'rgba(52, 211, 153, 0.15)',
                    color: '#34D399',
                    cursor: 'pointer',
                  }}
                  title="Exportar dados populacionais e ecológicos em CSV"
                >
                  <FileSpreadsheet size={12} /> Séries (.CSV)
                </button>
                <button
                  onClick={exportChronicleJSON}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    padding: '6px 8px',
                    fontSize: '10px',
                    fontWeight: 700,
                    borderRadius: '6px',
                    border: '1px solid rgba(56, 189, 248, 0.35)',
                    background: 'rgba(56, 189, 248, 0.15)',
                    color: '#38BDF8',
                    cursor: 'pointer',
                  }}
                  title="Exportar ensaio completo com eventos e métricas em JSON"
                >
                  <FileJson size={12} /> Ensaio (.JSON)
                </button>
              </div>
            </div>
          </>
        )}

        {/* ABA DE TERRITÓRIOS E DISPUTA POR RECURSOS */}
        {activeTab === 'territories' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Regiões & Qualidade Territorial ({territories.length})
              </span>
              <span style={{ fontSize: '10px', color: '#34D399', fontWeight: 600 }}>
                {territories.filter((t) => t.status === 'SETTLED').length} Ocupadas &bull; {territories.filter((t) => t.status === 'CONTESTED').length} Disputadas
              </span>
            </div>

            {/* Painel de Indicadores Macroeconômicos / Ecológicos */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                <div style={{ fontSize: '9px', color: '#94A3B8' }}>Assentadas</div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#34D399', marginTop: '2px' }}>
                  {territories.filter((t) => t.status === 'SETTLED').length}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                <div style={{ fontSize: '9px', color: '#94A3B8' }}>Disputadas</div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#F87171', marginTop: '2px' }}>
                  {territories.filter((t) => t.status === 'CONTESTED').length}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                <div style={{ fontSize: '9px', color: '#94A3B8' }}>Degradadas</div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#F59E0B', marginTop: '2px' }}>
                  {territories.filter((t) => t.status === 'DEGRADED').length}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                <div style={{ fontSize: '9px', color: '#94A3B8' }}>Qualidade</div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#38BDF8', marginTop: '2px' }}>
                  {territories.length > 0 ? (territories.reduce((acc, t) => acc + t.quality_score, 0) / territories.length).toFixed(0) : 0}%
                </div>
              </div>
            </div>

            {/* Lista Detalhada das 8 Zonas */}
            {territories.map((zone) => {
              const getStatusBadge = (st: string) => {
                switch (st) {
                  case 'SETTLED':
                    return { label: 'Assentada', color: '#34D399', bg: 'rgba(52, 211, 153, 0.15)', border: 'rgba(52, 211, 153, 0.4)' };
                  case 'CONTESTED':
                    return { label: 'Em Disputa', color: '#F87171', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.5)' };
                  case 'DEGRADED':
                    return { label: 'Degradada', color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.15)', border: 'rgba(148, 163, 184, 0.4)' };
                  case 'ABANDONED':
                    return { label: 'Pousio / Repouso', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)' };
                  case 'UNCLAIMED':
                  default:
                    return { label: 'Livre', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.3)' };
                }
              };

              const badge = getStatusBadge(zone.status);
              const qualityColor = zone.quality_score >= 60 ? '#34D399' : zone.quality_score >= 35 ? '#FBBF24' : '#F87171';

              return (
                <div
                  key={zone.id}
                  style={{
                    background: 'rgba(15, 23, 42, 0.75)',
                    border: `1px solid ${zone.status === 'CONTESTED' ? 'rgba(239, 68, 68, 0.5)' : 'rgba(255, 255, 255, 0.08)'}`,
                    borderRadius: '10px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  {/* Cabeçalho da Zona */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>
                          {zone.is_peripheral ? '🛡️' : '🌴'} {zone.name}
                        </span>
                        <span style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>
                          #{zone.id}
                        </span>
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                        {zone.is_peripheral ? 'Região Periférica / Santuário' : 'Oásis Central de Recursos'} &bull; Centro ({zone.x.toFixed(0)}, {zone.y.toFixed(0)})
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: '9px',
                        padding: '3px 8px',
                        borderRadius: '12px',
                        fontWeight: 700,
                        color: badge.color,
                        background: badge.bg,
                        border: `1px solid ${badge.border}`,
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>

                  {/* Barra de Qualidade Territorial */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '3px' }}>
                      <span style={{ color: '#94A3B8', fontWeight: 600 }}>Índice de Qualidade Ambiental</span>
                      <span style={{ fontWeight: 800, color: qualityColor, fontFamily: 'JetBrains Mono, monospace' }}>
                        {zone.quality_score.toFixed(1)} / 100
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '5px', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, zone.quality_score)}%`, height: '100%', background: qualityColor }} />
                    </div>
                  </div>

                  {/* Grid de 6 Indicadores Regionais */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Alimento / Biomassa</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#34D399', marginTop: '1px' }}>
                        🥩 {zone.food_count} ({zone.biomass.toFixed(0)} kcal)
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Fertilidade do Solo</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#FBBF24', marginTop: '1px' }}>
                        🌱 {zone.current_fertility.toFixed(2)}x
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Lotação / Suporte</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8', marginTop: '1px' }}>
                        👥 {zone.occupants_count} / {zone.carrying_capacity}
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Fauna Residente</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#E2E8F0', marginTop: '1px' }}>
                        🐇 {zone.vranco_count} &bull; 🐺 {zone.predator_count}
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Segurança Local</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: zone.safety_score >= 0.7 ? '#34D399' : '#F87171', marginTop: '1px' }}>
                        🛡️ {(zone.safety_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Competição</div>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: zone.competition_pressure > 0.5 ? '#F87171' : '#CBD5E1', marginTop: '1px' }}>
                        ⚡ {(zone.competition_pressure * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Histórico Recente de Ocorrências na Zona */}
                  {zone.history_log && zone.history_log.length > 0 && (
                    <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '6px 8px', borderRadius: '6px', fontSize: '9px', color: '#94A3B8' }}>
                      <div style={{ fontWeight: 700, color: '#E2E8F0', marginBottom: '2px' }}>
                        Histórico Recente de Ocupação:
                      </div>
                      {zone.history_log.slice(-2).map((h, i) => (
                        <div key={i} style={{ display: 'flex', gap: '4px', marginTop: '2px' }}>
                          <span style={{ color: '#FBBF24', fontFamily: 'JetBrains Mono, monospace' }}>#{h.tick}</span>
                          <span>{h.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
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
                                {relIcon} Clã #{targetClanId}: {String(rel)}
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

                    {/* Botão de Atalho para a Crônica Histórica deste Clã */}
                    <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '6px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => {
                          setChronicleClan(String(clan.id));
                          setActiveTab('chronicle');
                          setSelectedChronicleEvent(null);
                        }}
                        style={{
                          background: 'rgba(245, 158, 11, 0.12)',
                          border: '1px solid rgba(245, 158, 11, 0.3)',
                          borderRadius: '5px',
                          color: '#FBBF24',
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '4px 8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <BookOpen size={11} /> Consultar Anais na Crônica &rarr;
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* ABA DA CRÔNICA HISTÓRICA DO ECOSSISTEMA */}
        {activeTab === 'chronicle' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Header da Crônica */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%)',
                border: '1px solid rgba(234, 179, 8, 0.3)',
                borderRadius: '10px',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={16} color="#FBBF24" />
                  <strong style={{ fontSize: '13px', color: '#F8FAFC' }}>Crônica Histórica do Ecossistema</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '10px', color: '#94A3B8', background: 'rgba(255, 255, 255, 0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                    {chronicleTotal} registros
                  </span>
                  <button
                    onClick={fetchChronicle}
                    disabled={chronicleLoading}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#FBBF24',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '2px',
                    }}
                    title="Atualizar Crônica"
                  >
                    <RefreshCw size={13} className={chronicleLoading ? 'spin' : ''} />
                  </button>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#94A3B8', lineHeight: '1.4' }}>
                Registro contínuo e factual de todos os nascimentos, lideranças, conflitos de clãs, migrações territoriais e transições climáticas.
              </div>
            </div>

            {/* Painel de Filtros e Busca */}
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '10px 12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {/* Barra de Pesquisa */}
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={13} color="#94A3B8" style={{ position: 'absolute', left: '8px' }} />
                <input
                  type="text"
                  placeholder="Pesquisar indivíduo, clã, motivo ou causa..."
                  value={chronicleSearch}
                  onChange={(e) => setChronicleSearch(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    padding: '6px 26px 6px 28px',
                    color: '#F8FAFC',
                    fontSize: '11px',
                    outline: 'none',
                  }}
                />
                {chronicleSearch && (
                  <button
                    onClick={() => setChronicleSearch('')}
                    style={{
                      position: 'absolute',
                      right: '6px',
                      background: 'transparent',
                      border: 'none',
                      color: '#94A3B8',
                      cursor: 'pointer',
                    }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>

              {/* Filtros em Linha: Espécie, Categoria, Clã */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                {/* Filtro de Espécie */}
                <select
                  value={chronicleSpecies}
                  onChange={(e) => setChronicleSpecies(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#F8FAFC',
                    fontSize: '10px',
                    padding: '5px 6px',
                    outline: 'none',
                  }}
                >
                  <option value="all">Todas as Espécies</option>
                  <option value="PREDATOR">Predadores</option>
                  <option value="VRANCO">Vrancos</option>
                </select>

                {/* Filtro de Categoria de Evento */}
                <select
                  value={chronicleCategory}
                  onChange={(e) => setChronicleCategory(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#F8FAFC',
                    fontSize: '10px',
                    padding: '5px 6px',
                    outline: 'none',
                  }}
                >
                  <option value="all">Todas as Categorias</option>
                  <option value="BIRTH">🐣 Nascimentos & Gênese</option>
                  <option value="DEATH">💀 Mortes & Falecimentos</option>
                  <option value="LEADERSHIP_ELECTED">👑 Eleições de Líder Alpha/Beta</option>
                  <option value="LEADERSHIP_DEPOSED">🚪 Deserções & Queda de Líder</option>
                  <option value="CLAN_FOUNDED">🏰 Fundação de Clãs</option>
                  <option value="CLAN_STAGE_CHANGE">📈 Evolução Social de Clã</option>
                  <option value="WAR_DECLARED">⚔️ Declarações de Guerra</option>
                  <option value="TRUCE_SIGNED">🕊️ Tréguas & Armistícios</option>
                  <option value="TERRITORY_CONTESTED">🗺️ Disputas Territoriais</option>
                  <option value="TERRITORY_LOST">🛡️ Recuos Pacíficos</option>
                  <option value="MIGRATION">🧭 Migrações por Escassez</option>
                  <option value="MOBBING_DEFENSE">🦅 Defesas Coletivas dos Vrancos</option>
                  <option value="ENVIRONMENTAL_SEASON">❄️ Transições Climáticas</option>
                  <option value="SPECIES_EXTINCTION">⚠️ Extinções</option>
                  <option value="CULTURAL_LOSS">🧠 Perdas Culturais</option>
                </select>
              </div>

              {/* Filtro de Clã e Importância */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '6px', alignItems: 'center' }}>
                <select
                  value={chronicleClan}
                  onChange={(e) => setChronicleClan(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#F8FAFC',
                    fontSize: '10px',
                    padding: '5px 6px',
                    outline: 'none',
                  }}
                >
                  <option value="all">Todos os Clãs</option>
                  {clans.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.name}
                    </option>
                  ))}
                </select>

                {/* Seletor de Importância Mínima */}
                <div style={{ display: 'flex', gap: '3px' }}>
                  {[1, 3, 4, 5].map((imp) => (
                    <button
                      key={imp}
                      onClick={() => setChronicleImportance(imp)}
                      style={{
                        flex: 1,
                        padding: '4px 0',
                        fontSize: '9px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        border: 'none',
                        background: chronicleImportance === imp ? 'rgba(245, 158, 11, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                        color: chronicleImportance === imp ? '#FBBF24' : '#94A3B8',
                        cursor: 'pointer',
                      }}
                      title={`Importância mínima ${imp}`}
                    >
                      ★{imp}+
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Visualizador de Detalhes do Evento Selecionado (Inspeção Profunda) */}
            {selectedChronicleEvent && (
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'rgba(245, 158, 11, 0.15)',
                          color: '#FBBF24',
                        }}
                      >
                        {selectedChronicleEvent.event_type}
                      </span>
                      <span style={{ fontSize: '10px', color: '#94A3B8' }}>
                        Ano {selectedChronicleEvent.year} • Ciclo {selectedChronicleEvent.tick}
                      </span>
                      <span style={{ fontSize: '10px', color: '#FBBF24' }}>
                        {'★'.repeat(selectedChronicleEvent.importance)}
                      </span>
                    </div>
                    <strong style={{ fontSize: '13px', color: '#F8FAFC', marginTop: '2px' }}>
                      {selectedChronicleEvent.title}
                    </strong>
                  </div>
                  <button
                    onClick={() => setSelectedChronicleEvent(null)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: 'none',
                      borderRadius: '4px',
                      color: '#94A3B8',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                  >
                    <X size={14} />
                  </button>
                </div>

                <div style={{ fontSize: '11px', color: '#CBD5E1', lineHeight: '1.4' }}>
                  {selectedChronicleEvent.description}
                </div>

                {/* Caixa de Causa e Efeito Factual */}
                <div
                  style={{
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                    fontSize: '11px',
                  }}
                >
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{ color: '#F59E0B', fontWeight: 700 }}>🔍 Causa Registrada:</span>
                    <span style={{ color: '#E2E8F0' }}>{selectedChronicleEvent.cause}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{ color: '#38BDF8', fontWeight: 700 }}>⚖️ Resultado Concreto:</span>
                    <span style={{ color: '#E2E8F0' }}>{selectedChronicleEvent.result}</span>
                  </div>
                </div>

                {/* Participantes Envolvidos */}
                {(selectedChronicleEvent.primary_organism_id || selectedChronicleEvent.clan_name) && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', color: '#94A3B8' }}>Envolvidos:</span>
                    {selectedChronicleEvent.primary_organism_id && (
                      <button
                        onClick={() => onSelectOrganism(selectedChronicleEvent.primary_organism_id!)}
                        style={{
                          background: 'rgba(56, 189, 248, 0.15)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          borderRadius: '4px',
                          color: '#38BDF8',
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '2px 6px',
                          cursor: 'pointer',
                        }}
                      >
                        {selectedChronicleEvent.primary_organism_name || `Animal #${selectedChronicleEvent.primary_organism_id}`} &rarr;
                      </button>
                    )}
                    {selectedChronicleEvent.clan_name && (
                      <span
                        style={{
                          background: 'rgba(245, 158, 11, 0.15)',
                          border: '1px solid rgba(245, 158, 11, 0.3)',
                          borderRadius: '4px',
                          color: '#FBBF24',
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '2px 6px',
                        }}
                      >
                        🏰 {selectedChronicleEvent.clan_name}
                      </span>
                    )}
                  </div>
                )}

                {/* Eventos Correlatos / Encadeamento Causal */}
                {selectedChronicleEvent.related_event_ids && selectedChronicleEvent.related_event_ids.length > 0 && (
                  <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '8px', marginTop: '2px' }}>
                    <div style={{ fontSize: '10px', fontWeight: 700, color: '#C084FC', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
                      <CornerDownRight size={11} /> Acontecimentos Correlatos / Nexo Causal ({selectedChronicleEvent.related_event_ids.length})
                    </div>
                    {detailLoading ? (
                      <div style={{ fontSize: '10px', color: '#94A3B8' }}>Carregando conexões...</div>
                    ) : relatedChronicleEvents.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {relatedChronicleEvents.map((rel) => (
                          <div
                            key={rel.id}
                            onClick={() => handleInspectChronicleEvent(rel)}
                            style={{
                              background: 'rgba(168, 85, 247, 0.08)',
                              border: '1px solid rgba(168, 85, 247, 0.25)',
                              borderRadius: '6px',
                              padding: '6px 8px',
                              cursor: 'pointer',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                              <span style={{ fontSize: '10px', fontWeight: 600, color: '#F8FAFC' }}>
                                {rel.title}
                              </span>
                              <span style={{ fontSize: '9px', color: '#94A3B8' }}>
                                T#{rel.tick} • {rel.cause}
                              </span>
                            </div>
                            <ArrowRight size={12} color="#C084FC" />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: '10px', color: '#64748B' }}>Eventos arquivados ou prévios.</div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Feed da Linha do Tempo */}
            {chronicleLoading ? (
              <div style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '12px' }}>
                Consultando anais da Crônica Histórica...
              </div>
            ) : chronicleEvents.length === 0 ? (
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px dashed rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  padding: '24px 16px',
                  textAlign: 'center',
                  color: 'var(--color-text-muted)',
                  fontSize: '11px',
                }}
              >
                Nenhum acontecimento registrado para os filtros selecionados.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {chronicleEvents.map((event) => {
                  const getCategoryColor = (type: string) => {
                    switch (type) {
                      case 'BIRTH':
                        return { color: '#34D399', bg: 'rgba(52, 211, 153, 0.12)' };
                      case 'DEATH':
                        return { color: '#F87171', bg: 'rgba(248, 113, 113, 0.12)' };
                      case 'CLAN_FOUNDED':
                      case 'CLAN_STAGE_CHANGE':
                      case 'LEADERSHIP_ELECTED':
                        return { color: '#FBBF24', bg: 'rgba(245, 158, 11, 0.12)' };
                      case 'WAR_DECLARED':
                      case 'COMBAT_ENGAGEMENT':
                        return { color: '#FB7185', bg: 'rgba(251, 113, 133, 0.12)' };
                      case 'TRUCE_SIGNED':
                      case 'MOBBING_DEFENSE':
                        return { color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.12)' };
                      case 'MIGRATION':
                      case 'TERRITORY_LOST':
                        return { color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)' };
                      case 'ENVIRONMENTAL_SEASON':
                      case 'SPECIES_EXTINCTION':
                        return { color: '#A855F7', bg: 'rgba(168, 85, 247, 0.12)' };
                      default:
                        return { color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.12)' };
                    }
                  };

                  const catStyle = getCategoryColor(event.event_type);
                  const isSelected = selectedChronicleEvent?.id === event.id;

                  return (
                    <div
                      key={event.id}
                      onClick={() => handleInspectChronicleEvent(event)}
                      style={{
                        background: isSelected ? 'rgba(30, 41, 59, 0.9)' : 'rgba(15, 23, 42, 0.75)',
                        border: isSelected
                          ? '1px solid #FBBF24'
                          : event.importance >= 4
                          ? '1px solid rgba(245, 158, 11, 0.35)'
                          : '1px solid rgba(255, 255, 255, 0.06)',
                        borderRadius: '8px',
                        padding: '10px 12px',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.borderColor = event.importance >= 4
                            ? 'rgba(245, 158, 11, 0.35)'
                            : 'rgba(255, 255, 255, 0.06)';
                        }
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span
                            style={{
                              fontSize: '9px',
                              fontWeight: 700,
                              padding: '2px 5px',
                              borderRadius: '4px',
                              background: catStyle.bg,
                              color: catStyle.color,
                            }}
                          >
                            {event.event_type}
                          </span>
                          <span style={{ fontSize: '9px', color: '#FBBF24' }}>
                            {'★'.repeat(event.importance)}
                          </span>
                        </div>
                        <span style={{ fontSize: '10px', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <Clock size={10} /> Ano {event.year} • T#{event.tick}
                        </span>
                      </div>

                      <div style={{ fontSize: '11px', fontWeight: 600, color: '#F8FAFC' }}>
                        {event.title}
                      </div>

                      <div style={{ fontSize: '10px', color: '#94A3B8', lineHeight: '1.3' }}>
                        {event.description}
                      </div>

                      {/* Callout de Causa e Efeito */}
                      <div
                        style={{
                          background: 'rgba(0, 0, 0, 0.25)',
                          borderRadius: '4px',
                          padding: '5px 8px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '3px',
                          fontSize: '10px',
                        }}
                      >
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <span style={{ color: '#F59E0B', fontWeight: 600 }}>Causa:</span>
                          <span style={{ color: '#E2E8F0' }}>{event.cause}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <span style={{ color: '#38BDF8', fontWeight: 600 }}>Resultado:</span>
                          <span style={{ color: '#E2E8F0' }}>{event.result}</span>
                        </div>
                      </div>

                      {/* Rodapé do Card */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9px', color: '#64748B' }}>
                          {event.clan_name && <span>🏰 {event.clan_name}</span>}
                          {event.species && <span>• {event.species}</span>}
                        </div>
                        {event.related_event_ids && event.related_event_ids.length > 0 && (
                          <span style={{ fontSize: '9px', color: '#C084FC', display: 'flex', alignItems: 'center', gap: '2px' }}>
                            <CornerDownRight size={10} /> {event.related_event_ids.length} conexões
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'evolution' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Header / Visão da Dinâmica Evolutiva */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
                border: '1px solid rgba(168, 85, 247, 0.25)',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Dna size={16} color="#C084FC" />
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>
                    Painel de Evolução & Genética Populacional
                  </span>
                </div>
                <span style={{ fontSize: '10px', color: '#94A3B8' }}>
                  Pop: {metrics?.population ?? 0} • Gen Máx: {metrics?.max_generation ?? 0}
                </span>
              </div>

              {/* Indicadores de Diversidade e Endogamia */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '9px', color: '#94A3B8' }}>Heterozigosidade Média</span>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#38BDF8' }}>
                    {((metrics?.evolution?.genetic_diversity?.average_heterozygosity ?? 0.5) * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '9px', color: '#94A3B8' }}>Consanguinidade Média (F)</span>
                  <div
                    style={{
                      fontSize: '13px',
                      fontWeight: 700,
                      color: (metrics?.evolution?.genetic_diversity?.average_inbreeding_coefficient ?? 0) > 0.05 ? '#F87171' : '#34D399',
                    }}
                  >
                    F = {(metrics?.evolution?.genetic_diversity?.average_inbreeding_coefficient ?? 0).toFixed(3)}
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '9px', color: '#94A3B8' }}>Tam. Efetivo Pop. (Ne)</span>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#FBBF24' }}>
                    {metrics?.evolution?.genetic_diversity?.effective_population_size ?? 0}
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '9px', color: '#94A3B8' }}>Linhagens Ativas</span>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#C084FC' }}>
                    {metrics?.evolution?.genetic_diversity?.unique_lineages ?? 0} linhagens
                  </div>
                </div>
              </div>
            </div>

            {/* Gráfico de Dispersão Fenotípica em Tempo Real (Velocidade vs Força) */}
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(168, 85, 247, 0.25)',
                borderRadius: '8px',
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BarChart2 size={13} color="#C084FC" />
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC' }}>
                    Dispersão Fenotípica (Velocidade x Força)
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '6px', fontSize: '9px' }}>
                  <span style={{ color: '#F59E0B' }}>● Vranco</span>
                  <span style={{ color: '#EF4444' }}>● Predador</span>
                </div>
              </div>

              {/* Scatter Plot SVG */}
              <div style={{ position: 'relative', width: '100%', height: '170px' }}>
                <svg
                  width="100%"
                  height="170"
                  viewBox="0 0 300 170"
                  style={{ overflow: 'visible', background: 'rgba(10, 15, 26, 0.65)', borderRadius: '6px' }}
                >
                  {/* Grid Lines */}
                  <line x1="32" y1="18" x2="32" y2="145" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
                  <line x1="32" y1="145" x2="290" y2="145" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
                  <line x1="32" y1="81" x2="290" y2="81" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                  <line x1="161" y1="18" x2="161" y2="145" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />

                  {/* Quadrant Hints */}
                  <text x="36" y="28" fill="rgba(255,255,255,0.25)" fontSize="8">Tanque</text>
                  <text x="245" y="28" fill="rgba(255,255,255,0.25)" fontSize="8">Apex / Alpha</text>
                  <text x="36" y="140" fill="rgba(255,255,255,0.25)" fontSize="8">Adaptativo</text>
                  <text x="240" y="140" fill="rgba(255,255,255,0.25)" fontSize="8">Ágil / Coletor</text>

                  {/* Axis Labels */}
                  <text x="12" y="85" fill="#94A3B8" fontSize="8" transform="rotate(-90 12,85)" textAnchor="middle">
                    Força
                  </text>
                  <text x="161" y="162" fill="#94A3B8" fontSize="8" textAnchor="middle">
                    Velocidade (v)
                  </text>

                  {/* Points */}
                  {organisms.map((org) => {
                    const plotW = 258;
                    const plotH = 127;
                    const minX = 32;
                    const minY = 18;
                    const maxV = 6.0;
                    const maxF = 45.0;

                    const cx = minX + Math.min(plotW, Math.max(0, ((org.v || 1.5) / maxV) * plotW));
                    const cy = minY + plotH - Math.min(plotH, Math.max(0, ((org.f || 15) / maxF) * plotH));
                    const isVranco = org.sp === 'V';
                    const isHovered = hoveredScatterOrg?.id === org.id;

                    return (
                      <g
                        key={org.id}
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={() => setHoveredScatterOrg(org)}
                        onMouseLeave={() => setHoveredScatterOrg(null)}
                        onClick={() => onSelectOrganism(org.id)}
                      >
                        {isHovered && (
                          <circle
                            cx={cx}
                            cy={cy}
                            r="8"
                            fill="none"
                            stroke={isVranco ? '#F59E0B' : '#EF4444'}
                            strokeWidth="1.5"
                            opacity="0.8"
                          />
                        )}
                        <circle
                          cx={cx}
                          cy={cy}
                          r={isHovered ? 5 : 3.5}
                          fill={isVranco ? '#F59E0B' : (org.r === 'F' ? '#FB7185' : '#EF4444')}
                          stroke="rgba(0,0,0,0.6)"
                          strokeWidth="0.8"
                        />
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* Hover Tooltip or Stats Summary */}
              {hoveredScatterOrg ? (
                <div
                  style={{
                    background: 'rgba(0, 0, 0, 0.4)',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <span style={{ color: '#F8FAFC', fontWeight: 600 }}>
                    {hoveredScatterOrg.sp === 'V' ? '⚡ Vranco' : '🐺 Predador'} #{hoveredScatterOrg.id} ({hoveredScatterOrg.r})
                  </span>
                  <div style={{ display: 'flex', gap: '8px', color: '#94A3B8' }}>
                    <span>Vel: <strong style={{ color: '#38BDF8' }}>{hoveredScatterOrg.v?.toFixed(1) ?? '—'}</strong></span>
                    <span>Força: <strong style={{ color: '#F59E0B' }}>{hoveredScatterOrg.f?.toFixed(1) ?? '—'}</strong></span>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '9px', color: '#64748B', textAlign: 'center' }}>
                  Passe o mouse sobre um indivíduo para inspecionar seu fenótipo ou clique para rastrear.
                </div>
              )}
            </div>

            {/* Painel de Comparação de Gerações (Pioneiros G0 vs Geração Atual) */}
            {metrics?.evolution?.generations && metrics.evolution.generations[0] && (metrics.max_generation ?? 0) > 0 && (
              (() => {
                const gen0 = metrics.evolution.generations[0];
                const curGen = metrics.evolution.generations[metrics.max_generation ?? 0] || gen0;
                const dForca = curGen.avg_forca - gen0.avg_forca;
                const dVel = curGen.avg_velocidade - gen0.avg_velocidade;
                const dRes = curGen.avg_resistencia - gen0.avg_resistencia;
                const dCol = curGen.avg_coleta - gen0.avg_coleta;

                return (
                  <div
                    style={{
                      background: 'rgba(15, 23, 42, 0.65)',
                      border: '1px solid rgba(16, 185, 129, 0.25)',
                      borderRadius: '8px',
                      padding: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <TrendingUp size={13} color="#34D399" />
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC' }}>
                          Deriva & Seleção: G0 vs G{metrics.max_generation}
                        </span>
                      </div>
                      <span style={{ fontSize: '9px', padding: '2px 5px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', fontWeight: 700 }}>
                        {metrics.max_generation} gerações
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', textAlign: 'center', fontSize: '9px' }}>
                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 4px', borderRadius: '4px' }}>
                        <div style={{ color: '#94A3B8' }}>Força</div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: dForca >= 0 ? '#34D399' : '#F87171', marginTop: '2px' }}>
                          {dForca >= 0 ? `+${dForca.toFixed(1)}` : dForca.toFixed(1)}
                        </div>
                        <div style={{ fontSize: '8px', color: '#64748B' }}>{gen0.avg_forca.toFixed(1)} &rarr; {curGen.avg_forca.toFixed(1)}</div>
                      </div>

                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 4px', borderRadius: '4px' }}>
                        <div style={{ color: '#94A3B8' }}>Velocidade</div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: dVel >= 0 ? '#34D399' : '#F87171', marginTop: '2px' }}>
                          {dVel >= 0 ? `+${dVel.toFixed(1)}` : dVel.toFixed(1)}
                        </div>
                        <div style={{ fontSize: '8px', color: '#64748B' }}>{gen0.avg_velocidade.toFixed(1)} &rarr; {curGen.avg_velocidade.toFixed(1)}</div>
                      </div>

                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 4px', borderRadius: '4px' }}>
                        <div style={{ color: '#94A3B8' }}>Resistência</div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: dRes >= 0 ? '#34D399' : '#F87171', marginTop: '2px' }}>
                          {dRes >= 0 ? `+${dRes.toFixed(1)}` : dRes.toFixed(1)}
                        </div>
                        <div style={{ fontSize: '8px', color: '#64748B' }}>{gen0.avg_resistencia.toFixed(1)} &rarr; {curGen.avg_resistencia.toFixed(1)}</div>
                      </div>

                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 4px', borderRadius: '4px' }}>
                        <div style={{ color: '#94A3B8' }}>Coleta</div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: dCol >= 0 ? '#34D399' : '#F87171', marginTop: '2px' }}>
                          {dCol >= 0 ? `+${dCol.toFixed(1)}` : dCol.toFixed(1)}
                        </div>
                        <div style={{ fontSize: '8px', color: '#64748B' }}>{gen0.avg_coleta.toFixed(1)} &rarr; {curGen.avg_coleta.toFixed(1)}</div>
                      </div>
                    </div>
                  </div>
                );
              })()
            )}

            {/* Evolução de Atributos por Geração */}
            <div>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Médias Alélicas por Geração
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                {metrics?.evolution?.generations && Object.keys(metrics.evolution.generations).length > 0 ? (
                  Object.values(metrics.evolution.generations).map((g) => (
                    <div
                      key={g.generation}
                      style={{
                        background: 'rgba(15, 23, 42, 0.6)',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#F8FAFC' }}>
                          Geração {g.generation}
                        </span>
                        <span style={{ fontSize: '10px', color: '#94A3B8' }}>
                          {g.alive} vivos / {g.total_born} nascidos
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', fontSize: '9px', textAlign: 'center' }}>
                        <div style={{ background: 'rgba(244, 63, 94, 0.1)', padding: '3px', borderRadius: '4px', color: '#FDA4AF' }}>
                          Força: <strong>{g.avg_forca.toFixed(1)}</strong>
                        </div>
                        <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '3px', borderRadius: '4px', color: '#7DD3FC' }}>
                          Velocidade: <strong>{g.avg_velocidade.toFixed(1)}</strong>
                        </div>
                        <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '3px', borderRadius: '4px', color: '#6EE7B7' }}>
                          Resistência: <strong>{g.avg_resistencia.toFixed(1)}</strong>
                        </div>
                        <div style={{ background: 'rgba(168, 85, 247, 0.1)', padding: '3px', borderRadius: '4px', color: '#D8B4FE' }}>
                          Coleta: <strong>{g.avg_coleta.toFixed(1)}</strong>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '11px', color: '#64748B', textAlign: 'center', padding: '12px' }}>
                    Coletando dados intergeracionais...
                  </div>
                )}
              </div>
            </div>

            {/* Linhagens Ativas */}
            <div>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Linhagens Familiares no Ecossistema
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                {metrics?.evolution?.lineages && metrics.evolution.lineages.length > 0 ? (
                  metrics.evolution.lineages.map((lin) => (
                    <div
                      key={lin.id}
                      style={{
                        background: 'rgba(15, 23, 42, 0.5)',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#F8FAFC' }}>
                          {lin.name}
                        </div>
                        <div style={{ fontSize: '9px', color: '#94A3B8' }}>
                          ID: {lin.id} • Gen Média: {lin.avg_generation.toFixed(1)}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, color: '#38BDF8' }}>
                          {lin.active_members} animais
                        </span>
                        <div style={{ fontSize: '9px', color: '#A855F7' }}>
                          Het: {(lin.avg_heterozygosity * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '11px', color: '#64748B', textAlign: 'center', padding: '10px' }}>
                    Nenhuma linhagem ativa registrada.
                  </div>
                )}
              </div>
            </div>

            {/* Mortalidade por Causa */}
            <div>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Mortalidade Populacional por Causa
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginTop: '6px' }}>
                {metrics?.evolution?.mortality_by_cause && Object.keys(metrics.evolution.mortality_by_cause).length > 0 ? (
                  Object.entries(metrics.evolution.mortality_by_cause).map(([cause, count]) => (
                    <div
                      key={cause}
                      style={{
                        background: 'rgba(244, 63, 94, 0.08)',
                        border: '1px solid rgba(244, 63, 94, 0.2)',
                        padding: '6px',
                        borderRadius: '6px',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '9px', color: '#94A3B8' }}>{cause}</div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#FDA4AF' }}>{count}</div>
                    </div>
                  ))
                ) : (
                  <div style={{ gridColumn: 'span 3', fontSize: '11px', color: '#64748B', textAlign: 'center', padding: '8px' }}>
                    Nenhum óbito registrado até o momento.
                  </div>
                )}
              </div>
            </div>

            {/* Correlação Estatística de Sobrevivência */}
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                Correlação de Sobrevivência (Adultos Vivos vs Falecidos)
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10px' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px 8px', borderRadius: '4px' }}>
                  <div style={{ color: '#94A3B8' }}>Força Média</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                    <span style={{ color: '#34D399' }}>Vivos: {metrics?.evolution?.trait_survival_correlation?.surviving_adults_avg_forca?.toFixed(1) ?? '—'}</span>
                    <span style={{ color: '#F87171' }}>Óbitos: {metrics?.evolution?.trait_survival_correlation?.deceased_avg_forca?.toFixed(1) ?? '—'}</span>
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '6px 8px', borderRadius: '4px' }}>
                  <div style={{ color: '#94A3B8' }}>Velocidade Média</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                    <span style={{ color: '#34D399' }}>Vivos: {metrics?.evolution?.trait_survival_correlation?.surviving_adults_avg_velocidade?.toFixed(1) ?? '—'}</span>
                    <span style={{ color: '#F87171' }}>Óbitos: {metrics?.evolution?.trait_survival_correlation?.deceased_avg_velocidade?.toFixed(1) ?? '—'}</span>
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '9px', color: '#64748B', fontStyle: 'italic', lineHeight: '1.3' }}>
                * Nota metodológica: Apresentado como evidência empírica observada no ambiente simulado, e não como prova mecânica direta de causalidade exclusiva.
              </div>
            </div>
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
                } else if (ev.type === 'vranco_collective_defense') {
                  badgeColor = '#F59E0B';
                  icon = '🛡️';
                  title = 'Defesa Coletiva (Mobbing)';
                  desc = `Bando de ${ev.participants_count || 4} Vrancos confrontou e repeliu ${ev.predator_name} (-${ev.damage} HP)!`;
                } else if (ev.type === 'predator_defeated') {
                  badgeColor = '#10B981';
                  icon = '⚡';
                  title = 'Predador Vencido / Abatido';
                  desc = `${ev.predator_name} foi derrotado pela união defensiva dos Vrancos!`;
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', marginTop: '4px' }}>
              {(
                [
                  { key: 'all', label: 'Todos' },
                  { key: 'V', label: '⚡ Vrancos' },
                  { key: 'P', label: '🐺 Predadores' },
                  { key: 'M', label: 'Machos' },
                  { key: 'F', label: 'Fêmeas' },
                  { key: 'C', label: 'Filhotes' },
                ] as const
              ).map((f) => (
                <button
                  key={f.key}
                  onClick={() => setInhabitantFilter(f.key)}
                  style={{
                    padding: '4px',
                    fontSize: '9px',
                    fontWeight: 700,
                    borderRadius: '5px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background:
                      inhabitantFilter === f.key
                        ? f.key === 'V'
                          ? 'rgba(245, 158, 11, 0.3)'
                          : f.key === 'P'
                          ? 'rgba(16, 185, 129, 0.3)'
                          : 'rgba(56, 189, 248, 0.25)'
                        : 'rgba(255, 255, 255, 0.04)',
                    color:
                      inhabitantFilter === f.key
                        ? f.key === 'V'
                          ? '#FDE047'
                          : f.key === 'P'
                          ? '#6EE7B7'
                          : '#38BDF8'
                        : 'var(--color-text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Lista Scrollável de Habitantes */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '280px', overflowY: 'auto' }}>
              {filteredOrganisms.map((org) => {
                const clan = getClanName(org.fam);
                const isVranco = org.sp === 'V';
                const roleDot = isVranco ? '#F59E0B' : (org.r === 'M' ? '#34D399' : org.r === 'F' ? '#FB7185' : '#C084FC');
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
                          <span style={{ fontSize: '10px' }}>{isVranco ? '⚡' : '🐺'}</span>
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
