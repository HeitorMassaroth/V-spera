import React, { useEffect, useState } from 'react';
import {
  X,
  Dna,
  Activity,
  Heart,
  Users,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Sparkles,
  Home,
  AlertTriangle,
  Package,
} from 'lucide-react';
import type {
  CompactOrganism,
  OrganismDetailResponse,
  AttributeStats,
  AnimalRecord,
} from '../types';

interface AnimalInspectorProps {
  organismId: number;
  liveOrganism?: CompactOrganism;
  populationAverages?: AttributeStats;
  onClose: () => void;
  onSelectOrganism: (id: number) => void;
}

export const AnimalInspector: React.FC<AnimalInspectorProps> = ({
  organismId,
  liveOrganism,
  populationAverages,
  onClose,
  onSelectOrganism,
}) => {
  const [data, setData] = useState<OrganismDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'status' | 'personality' | 'family' | 'tree'>('status');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`/api/simulation/organism/${organismId}`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Erro ${res.status}: Animal não encontrado.`);
        }
        return res.json();
      })
      .then((json: OrganismDetailResponse) => {
        if (isMounted) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Falha ao carregar perfil do animal');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [organismId]);

  const tree = data?.family_tree;
  const animal = tree?.animal;

  // Genome data: live organism or historical record
  const forca = liveOrganism?.f ?? animal?.genome.forca ?? 10;
  const vel = liveOrganism?.v ?? animal?.genome.velocidade ?? 2.5;
  const res = liveOrganism?.res ?? animal?.genome.resistencia ?? 10;
  const intel = liveOrganism?.i ?? animal?.genome.inteligencia ?? 10;
  const maxSaude = liveOrganism?.ms ?? animal?.genome.max_saude ?? 100;
  const currentSaude = liveOrganism?.s ?? data?.current_stats?.saude ?? (data?.is_alive ? 100 : 0);
  const currentEnergy = liveOrganism?.e ?? data?.current_stats?.energy ?? 0;
  const hunger = data?.current_stats?.hunger ?? Math.max(0, 100 - currentEnergy);
  const age = liveOrganism?.a ?? data?.current_stats?.age ?? 0;
  const role = liveOrganism?.r ?? (animal?.role ? animal.role[0] : 'M');
  const sex = liveOrganism?.sx ?? data?.current_stats?.sex ?? (animal?.sex ?? (role === 'F' ? 'F' : 'M'));
  const stage = liveOrganism?.st ?? data?.current_stats?.life_stage ?? (animal?.life_stage ?? 'ADULT');
  const currentState = data?.current_stats?.current_state ?? liveOrganism?.act ?? 'EXPLORANDO';
  const carriedFood = data?.current_stats?.carried_food ?? liveOrganism?.cf ?? 0;
  const lifeExpectancy = data?.current_stats?.life_expectancy ?? 1800;
  const generation = liveOrganism?.gen ?? animal?.generation ?? 0;
  const name = liveOrganism?.nm ?? animal?.name ?? `Animal #${organismId}`;
  const causeOfDeath = data?.current_stats?.cause_of_death ?? animal?.cause_of_death;
  const partnerId = liveOrganism?.prt ?? data?.current_stats?.partner_id ?? animal?.partner_id;
  const partnerBondDuration = data?.current_stats?.partner_bond_duration ?? animal?.partner_bond_duration ?? 0;
  const mourningTicks = data?.current_stats?.mourning_ticks ?? 0;
  const personality = data?.current_stats?.personality ?? animal?.personality;
  const memory = data?.current_stats?.memory;
  const nest = data?.current_stats?.nest;
  const clanId = liveOrganism?.cln ?? data?.current_stats?.clan_id;
  const clanRole = liveOrganism?.clr ?? data?.current_stats?.clan_role;
  const leadershipScore = data?.current_stats?.leadership_score;

  // Role info
  const getRoleBadge = (r: string) => {
    switch (r) {
      case 'F':
        return { label: 'Rosa (Fêmea)', bg: 'rgba(244, 63, 94, 0.2)', color: '#FDA4AF', border: 'rgba(244, 63, 94, 0.4)' };
      case 'M':
        return { label: 'Verde (Macho)', bg: 'rgba(16, 185, 129, 0.2)', color: '#6EE7B7', border: 'rgba(16, 185, 129, 0.4)' };
      case 'C':
        return { label: 'Roxo (Filhote)', bg: 'rgba(168, 85, 247, 0.2)', color: '#D8B4FE', border: 'rgba(168, 85, 247, 0.4)' };
      default:
        return { label: 'Animal', bg: 'rgba(255, 255, 255, 0.1)', color: '#FFFFFF', border: 'transparent' };
    }
  };

  const getStageBadge = (st: string) => {
    const s = st[0].toUpperCase();
    switch (s) {
      case 'N':
        return { label: 'Recém-nascido', color: '#C084FC', bg: 'rgba(192, 132, 252, 0.15)' };
      case 'D':
        return { label: 'Em Desenvolvimento', color: '#A855F7', bg: 'rgba(168, 85, 247, 0.15)' };
      case 'J':
        return { label: 'Jovem Aprendiz', color: '#818CF8', bg: 'rgba(129, 140, 248, 0.15)' };
      case 'I':
        return { label: 'Jovem Independente', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.15)' };
      case 'A':
      default:
        return { label: 'Adulto', color: '#34D399', bg: 'rgba(52, 211, 153, 0.15)' };
    }
  };

  const getStateDescription = (st: string) => {
    switch (st) {
      case 'PROCURANDO_COMIDA':
        return { label: 'Procurando Alimento', color: '#FBBF24' };
      case 'DESCANSANDO':
        return { label: 'Descansando no Ninho', color: '#94A3B8' };
      case 'CORTEJANDO':
        return { label: 'Cortejando Pretendente', color: '#FB7185' };
      case 'DEFENDENDO_NINHO':
        return { label: 'Defendendo Ninho & Filhotes', color: '#EF4444' };
      case 'FUGINDO':
        return { label: 'Fugindo em Pânico', color: '#F87171' };
      case 'PREDANDO':
        return { label: 'Caçando / Predando', color: '#DC2626' };
      case 'CUIDANDO_FILHOTES':
        return { label: 'Amamentando / Cuidando', color: '#A855F7' };
      case 'LEVANDO_COMIDA':
        return { label: 'Transportando Comida ao Ninho', color: '#10B981' };
      default:
        return { label: 'Explorando Ecossistema', color: '#38BDF8' };
    }
  };

  const roleBadge = getRoleBadge(role);
  const stageBadge = getStageBadge(stage);
  const stateDesc = getStateDescription(currentState);
  const popAverages = populationAverages || data?.population_averages;

  // Comparison helpers
  const renderComparisonBadge = (val: number, avg?: number) => {
    if (avg === undefined) return null;
    const diff = val - avg;
    if (Math.abs(diff) < 0.2) {
      return (
        <span style={{ fontSize: '10px', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '2px' }}>
          = Média ({avg.toFixed(1)})
        </span>
      );
    }
    if (diff > 0) {
      return (
        <span style={{ fontSize: '10px', color: '#34D399', display: 'flex', alignItems: 'center', gap: '2px', fontWeight: 600 }}>
          <TrendingUp size={11} /> +{diff.toFixed(1)} acima da média ({avg.toFixed(1)})
        </span>
      );
    }
    return (
      <span style={{ fontSize: '10px', color: '#F87171', display: 'flex', alignItems: 'center', gap: '2px', fontWeight: 600 }}>
        <TrendingDown size={11} /> {diff.toFixed(1)} abaixo da média ({avg.toFixed(1)})
      </span>
    );
  };

  const renderRelativeCard = (label: string, rec?: AnimalRecord | null, sublabel?: string) => {
    if (!rec) {
      return (
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px dashed rgba(255, 255, 255, 0.1)',
            padding: '8px 10px',
            borderRadius: '8px',
            fontSize: '11px',
            color: 'var(--color-text-muted)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontWeight: 600, color: '#64748B', marginBottom: '2px' }}>{label}</div>
          <span>Ancestral Desconhecido (Fundador Gen 0)</span>
        </div>
      );
    }

    const badge = getRoleBadge(rec.role ? rec.role[0] : 'M');
    return (
      <div
        onClick={() => onSelectOrganism(rec.id)}
        style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '8px 10px',
          borderRadius: '8px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          display: 'flex',
          flexDirection: 'column',
          gap: '3px',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)';
          e.currentTarget.style.transform = 'translateY(-1px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
            {label} {sublabel && `(${sublabel})`}
          </span>
          <span
            style={{
              fontSize: '9px',
              padding: '2px 5px',
              borderRadius: '4px',
              background: badge.bg,
              color: badge.color,
            }}
          >
            {badge.label.split(' ')[0]}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>
            {rec.name}
          </span>
          <span style={{ fontSize: '10px', color: '#38BDF8', display: 'flex', alignItems: 'center' }}>
            #{rec.id} <ChevronRight size={12} />
          </span>
        </div>
        <div style={{ fontSize: '9px', color: 'var(--color-text-muted)', display: 'flex', gap: '6px' }}>
          <span>Gen {rec.generation}</span>
          <span>Força: {rec.genome.forca.toFixed(1)}</span>
          <span>Velocidade: {rec.genome.velocidade.toFixed(1)}</span>
        </div>
      </div>
    );
  };

  return (
    <div
      className="glass-panel"
      style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        width: '410px',
        maxHeight: 'calc(100% - 32px)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '14px',
        boxShadow: '0 20px 45px rgba(0, 0, 0, 0.7), 0 0 1px 1px rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        overflow: 'hidden',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
      {/* Header com Nome, Papel e Fechar */}
      <div
        style={{
          padding: '14px 16px',
          background: 'rgba(15, 23, 42, 0.90)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '9px',
              background: roleBadge.bg,
              border: `1px solid ${roleBadge.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: roleBadge.color,
              fontWeight: 800,
              fontSize: '15px',
            }}
          >
            {role}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px', fontWeight: 800, color: '#F8FAFC' }}>
                {name}
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: roleBadge.bg,
                  color: roleBadge.color,
                  border: `1px solid ${roleBadge.border}`,
                }}
              >
                {roleBadge.label}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'flex', gap: '6px', marginTop: '2px', alignItems: 'center' }}>
              <span>ID #{organismId}</span>
              <span>&bull;</span>
              <span>Gen {generation}</span>
              <span>&bull;</span>
              <span>Sexo: {sex === 'F' ? '♀ Fêmea' : '♂ Macho'}</span>
              <span>&bull;</span>
              <span style={{ color: data?.is_alive ? '#34D399' : '#F87171', fontWeight: 600 }}>
                {data?.is_alive ? '● Ativo' : `† Falecido (${data?.current_stats?.cause_of_death || data?.family_tree?.animal?.cause_of_death || 'Inanição'})`}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title="Fechar painel"
        >
          <X size={18} />
        </button>
      </div>

      {/* Banner de Liderança Alpha / Beta */}
      {clanRole && (clanRole === 'A' || clanRole === 'ALPHA' || clanRole === 'B' || clanRole === 'BETA') && (
        <div
          style={{
            padding: '10px 16px',
            background:
              clanRole === 'A' || clanRole === 'ALPHA'
                ? 'linear-gradient(90deg, rgba(245, 158, 11, 0.25), rgba(251, 191, 36, 0.1))'
                : 'linear-gradient(90deg, rgba(56, 189, 248, 0.25), rgba(147, 197, 253, 0.1))',
            borderBottom:
              clanRole === 'A' || clanRole === 'ALPHA'
                ? '1px solid rgba(245, 158, 11, 0.4)'
                : '1px solid rgba(56, 189, 248, 0.4)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>
              {clanRole === 'A' || clanRole === 'ALPHA' ? '👑' : '⭐'}
            </span>
            <div>
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 800,
                  color:
                    clanRole === 'A' || clanRole === 'ALPHA' ? '#FDE68A' : '#BFDBFE',
                  letterSpacing: '0.04em',
                }}
              >
                {clanRole === 'A' || clanRole === 'ALPHA'
                  ? `ALPHA DO CLÃ #${clanId ?? ''}`
                  : `BETA DO CLÃ #${clanId ?? ''}`}
              </div>
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.7)' }}>
                {clanRole === 'A' || clanRole === 'ALPHA'
                  ? 'Líder supremo: define prioridades coletivas e coordena'
                  : 'Sub-líder: organiza execução e substituto imediato'}
              </div>
            </div>
          </div>
          {leadershipScore !== undefined && (
            <div style={{ textAlign: 'right' }}>
              <div
                style={{
                  fontSize: '15px',
                  fontWeight: 800,
                  color:
                    clanRole === 'A' || clanRole === 'ALPHA' ? '#FBBF24' : '#60A5FA',
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              >
                {leadershipScore.toFixed(1)}
              </div>
              <div style={{ fontSize: '8px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' }}>
                Índice Força
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tabs de Navegação */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(11, 17, 30, 0.6)',
        }}
      >
        <button
          onClick={() => setActiveTab('status')}
          style={{
            flex: 1,
            padding: '9px 4px',
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
            background: activeTab === 'status' ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
            color: activeTab === 'status' ? '#38BDF8' : 'var(--color-text-muted)',
            border: 'none',
            borderBottom: activeTab === 'status' ? '2px solid #38BDF8' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
          }}
        >
          <Activity size={12} /> Status
        </button>
        <button
          onClick={() => setActiveTab('personality')}
          style={{
            flex: 1,
            padding: '9px 4px',
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
            background: activeTab === 'personality' ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
            color: activeTab === 'personality' ? '#38BDF8' : 'var(--color-text-muted)',
            border: 'none',
            borderBottom: activeTab === 'personality' ? '2px solid #38BDF8' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
          }}
        >
          <Sparkles size={12} /> Psique
        </button>
        <button
          onClick={() => setActiveTab('family')}
          style={{
            flex: 1,
            padding: '9px 4px',
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
            background: activeTab === 'family' ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
            color: activeTab === 'family' ? '#38BDF8' : 'var(--color-text-muted)',
            border: 'none',
            borderBottom: activeTab === 'family' ? '2px solid #38BDF8' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
          }}
        >
          <Heart size={12} /> Família & Ninho
        </button>
        <button
          onClick={() => setActiveTab('tree')}
          style={{
            flex: 1,
            padding: '9px 4px',
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
            background: activeTab === 'tree' ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
            color: activeTab === 'tree' ? '#38BDF8' : 'var(--color-text-muted)',
            border: 'none',
            borderBottom: activeTab === 'tree' ? '2px solid #38BDF8' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
          }}
        >
          <Users size={12} /> Linhagem
        </button>
      </div>

      {/* Conteúdo com Scroll */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {loading && (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '13px' }}>
            Consultando registros biométricos e histórico familiar...
          </div>
        )}

        {error && (
          <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: '#F87171', borderRadius: '8px', fontSize: '12px' }}>
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* TAB 1: STATUS & FISIOLOGIA */}
            {activeTab === 'status' && (
              <>
                {/* Alerta de Causa da Morte se falecido */}
                {causeOfDeath && (
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.12)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      color: '#F87171',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}
                  >
                    <AlertTriangle size={15} />
                    <span>Causa do Falecimento: {causeOfDeath} (Idade: {age} ticks)</span>
                  </div>
                )}

                {/* Badges de Estágio e Atividade Atual */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div
                    style={{
                      background: stageBadge.bg,
                      border: `1px solid ${stageBadge.color}40`,
                      padding: '8px 10px',
                      borderRadius: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px',
                    }}
                  >
                    <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Estágio de Vida
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 800, color: stageBadge.color }}>
                      {stageBadge.label}
                    </span>
                  </div>

                  <div
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      padding: '8px 10px',
                      borderRadius: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px',
                    }}
                  >
                    <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Estado / Atividade
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 800, color: stateDesc.color }}>
                      {stateDesc.label}
                    </span>
                  </div>
                </div>

                {/* Transporte de Alimento (se houver) */}
                {carriedFood > 0 && (
                  <div
                    style={{
                      background: 'rgba(16, 185, 129, 0.12)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      color: '#34D399',
                      fontSize: '11px',
                      fontWeight: 700,
                    }}
                  >
                    <Package size={14} />
                    <span>Transportando {carriedFood.toFixed(1)} kcal de alimento para o ninho familiar</span>
                  </div>
                )}

                {/* Barras de Saúde e Energia */}
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94A3B8', fontWeight: 600 }}>Saúde Física (HP)</span>
                      <span style={{ color: '#F8FAFC', fontWeight: 700 }}>
                        {currentSaude.toFixed(1)} / {maxSaude.toFixed(1)}
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '7px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.min(100, (currentSaude / maxSaude) * 100)}%`,
                          height: '100%',
                          background: currentSaude > maxSaude * 0.5 ? '#10B981' : currentSaude > maxSaude * 0.25 ? '#F59E0B' : '#EF4444',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94A3B8', fontWeight: 600 }}>Energia / Saturação</span>
                      <span style={{ color: '#F8FAFC', fontWeight: 700 }}>
                        {currentEnergy.toFixed(1)} kcal (Fome: {hunger.toFixed(1)}%)
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '7px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.min(100, currentEnergy)}%`,
                          height: '100%',
                          background: '#38BDF8',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Atributos Quantitativos Físicos */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Capacidade Física & Genômica
                  </span>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94A3B8' }}>Força Física</span>
                        <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>{forca.toFixed(1)}</span>
                      </div>
                      {renderComparisonBadge(forca, popAverages?.forca?.avg)}
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94A3B8' }}>Velocidade</span>
                        <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>{vel.toFixed(1)}</span>
                      </div>
                      {renderComparisonBadge(vel, popAverages?.velocidade?.avg)}
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94A3B8' }}>Resistência</span>
                        <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>{res.toFixed(1)}</span>
                      </div>
                      {renderComparisonBadge(res, popAverages?.resistencia?.avg)}
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94A3B8' }}>Inteligência</span>
                        <span style={{ fontSize: '13px', fontWeight: 800, color: '#F8FAFC' }}>{intel.toFixed(1)}</span>
                      </div>
                      {renderComparisonBadge(intel, popAverages?.inteligencia?.avg)}
                    </div>

                    {/* Card de Índice de Liderança do Habitante */}
                    {leadershipScore !== undefined && (
                      <div style={{ gridColumn: 'span 2', background: 'rgba(245, 158, 11, 0.08)', padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', color: '#FCD34D', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
                            👑 Índice de Liderança Coletiva
                          </span>
                          <span style={{ fontSize: '13px', fontWeight: 800, color: '#FBBF24', fontFamily: 'JetBrains Mono, monospace' }}>
                            {leadershipScore.toFixed(1)} / 100
                          </span>
                        </div>
                        <div style={{ width: '100%', height: '5px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', marginTop: '6px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, Math.max(0, leadershipScore))}%`,
                              height: '100%',
                              background: 'linear-gradient(90deg, #F59E0B, #FBBF24)',
                            }}
                          />
                        </div>
                        <div style={{ fontSize: '9px', color: 'rgba(255, 255, 255, 0.5)', marginTop: '4px' }}>
                          Base para eleição de Alpha e Beta (normalizado: força, velocidade, resistência, saúde, coleta e defesa).
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Expectativa de Vida e Eficiência */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '8px 10px', borderRadius: '8px' }}>
                    <span style={{ fontSize: '10px', color: '#94A3B8' }}>Idade Atual / Expectativa</span>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC' }}>
                      {age} / {lifeExpectancy} ticks
                    </div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '8px 10px', borderRadius: '8px' }}>
                    <span style={{ fontSize: '10px', color: '#94A3B8' }}>Eficiência de Coleta</span>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#34D399' }}>
                      {((personality?.eficiencia_coleta ?? 1.0) * 100).toFixed(0)}% de absorção
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* TAB 2: PSIQUE & PERSONALIDADE */}
            {activeTab === 'personality' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                  Perfil Psicológico & Tomada de Decisão
                </span>

                {personality ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {[
                      { key: 'instinto_protecao', label: 'Instinto de Proteção Parental', val: personality.instinto_protecao, color: '#34D399', desc: 'Prioriza defesa de ninho e alimentação de filhotes' },
                      { key: 'cautela', label: 'Cautela & Evasão de Riscos', val: personality.cautela, color: '#38BDF8', desc: 'Evita zonas de perigo recente e predadores' },
                      { key: 'sociabilidade', label: 'Sociabilidade & Cooperação', val: personality.sociabilidade, color: '#C084FC', desc: 'Tolerância no oásis, cooperação e facilidade de cortejo' },
                      { key: 'curiosidade', label: 'Curiosidade & Exploração', val: personality.curiosidade, color: '#FBBF24', desc: 'Explora novas regiões longe do ninho' },
                      { key: 'agressividade', label: 'Agressividade & Territorialismo', val: personality.agressividade, color: '#F87171', desc: 'Combatividade e disposição para lutar' },
                    ].map((item) => (
                      <div
                        key={item.key}
                        style={{
                          background: 'rgba(255, 255, 255, 0.02)',
                          padding: '10px',
                          borderRadius: '8px',
                          border: '1px solid rgba(255, 255, 255, 0.05)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                          <span style={{ color: '#F8FAFC', fontWeight: 700 }}>{item.label}</span>
                          <span style={{ color: item.color, fontWeight: 800 }}>{(item.val * 100).toFixed(0)}%</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${item.val * 100}%`, height: '100%', background: item.color }} />
                        </div>
                        <span style={{ fontSize: '10px', color: '#94A3B8', marginTop: '3px', display: 'block' }}>
                          {item.desc}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: '#64748B', fontSize: '12px', textAlign: 'center', padding: '20px' }}>
                    Dados de personalidade não disponíveis para este registro histórico.
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: FAMÍLIA, NINHO & MEMÓRIA */}
            {activeTab === 'family' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Vínculo Monogâmico Permanente */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Vínculo Conjugal Permanente
                  </span>
                  <div style={{ marginTop: '6px' }}>
                    {partnerId ? (
                      <div
                        onClick={() => onSelectOrganism(partnerId)}
                        style={{
                          background: 'rgba(244, 63, 94, 0.08)',
                          border: '1px solid rgba(244, 63, 94, 0.3)',
                          padding: '12px',
                          borderRadius: '10px',
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: '10px', color: '#FDA4AF', fontWeight: 700, textTransform: 'uppercase' }}>
                            💍 Parceiro Exclusivo Vitalício
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: 800, color: '#F8FAFC', marginTop: '2px' }}>
                            {tree?.partner ? tree.partner.name : `Parceiro #${partnerId}`}
                          </div>
                          <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>
                            Juntos há {partnerBondDuration} ticks &bull; Fidelidade Mútua
                          </div>
                        </div>
                        <ChevronRight size={16} color="#FDA4AF" />
                      </div>
                    ) : mourningTicks > 0 ? (
                      <div
                        style={{
                          background: 'rgba(245, 158, 11, 0.1)',
                          border: '1px dashed rgba(245, 158, 11, 0.4)',
                          padding: '10px 12px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          color: '#FCD34D',
                        }}
                      >
                        Período de luto pelo parceiro falecido ({mourningTicks} ticks restantes).
                      </div>
                    ) : (
                      <div
                        style={{
                          background: 'rgba(255, 255, 255, 0.02)',
                          border: '1px dashed rgba(255, 255, 255, 0.1)',
                          padding: '10px 12px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          color: 'var(--color-text-muted)',
                          textAlign: 'center',
                        }}
                      >
                        Solteiro &bull; Sem parceiro estabelecido no momento
                      </div>
                    )}
                  </div>
                </div>

                {/* Ninho Familiar */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Território & Ninho Familiar
                  </span>
                  <div style={{ marginTop: '6px' }}>
                    {nest ? (
                      <div
                        style={{
                          background: 'rgba(16, 185, 129, 0.08)',
                          border: '1px solid rgba(16, 185, 129, 0.25)',
                          padding: '12px',
                          borderRadius: '10px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '13px', fontWeight: 800, color: '#34D399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Home size={15} /> Ninho #{nest.id} (Nível {nest.level})
                          </span>
                          <span style={{ fontSize: '10px', background: 'rgba(52, 211, 153, 0.2)', color: '#34D399', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                            {nest.level === 3 ? 'Santuário Familiar' : nest.level === 2 ? 'Refúgio Fortificado' : 'Ninho Simples'}
                          </span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '2px', fontSize: '11px' }}>
                          <span style={{ color: '#94A3B8' }}>
                            Estoque Alimentos: <strong style={{ color: '#F8FAFC' }}>{nest.food_storage.toFixed(1)} kcal</strong>
                          </span>
                          <span style={{ color: '#94A3B8' }}>
                            Materiais: <strong style={{ color: '#F8FAFC' }}>{nest.materials.toFixed(1)}%</strong>
                          </span>
                          <span style={{ color: '#94A3B8' }}>
                            Localização: <strong style={{ color: '#F8FAFC' }}>({nest.x.toFixed(0)}, {nest.y.toFixed(0)})</strong>
                          </span>
                          <span style={{ color: '#94A3B8' }}>
                            Fundado no Tick: <strong style={{ color: '#F8FAFC' }}>#{nest.created_tick}</strong>
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div
                        style={{
                          background: 'rgba(255, 255, 255, 0.02)',
                          border: '1px dashed rgba(255, 255, 255, 0.1)',
                          padding: '10px 12px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          color: 'var(--color-text-muted)',
                          textAlign: 'center',
                        }}
                      >
                        Sem ninho próprio ativo &bull; Habitante nômade
                      </div>
                    )}
                  </div>
                </div>

                {/* Memória Episódica do Animal */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Memória de Experiências Marcantes
                  </span>
                  <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {memory && memory.danger_zones.length > 0 && (
                      <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '8px 10px', borderRadius: '6px', fontSize: '11px', color: '#FCA5A5' }}>
                        🛡️ <strong>{memory.danger_zones.length} Zonas de Perigo Evitadas</strong> (Locais de combate gravados na memória)
                      </div>
                    )}
                    {memory && memory.known_food_sources.length > 0 && (
                      <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '8px 10px', borderRadius: '6px', fontSize: '11px', color: '#7DD3FC' }}>
                        🌿 <strong>{memory.known_food_sources.length} Fontes de Alimento Lembradas</strong>
                      </div>
                    )}
                    {memory && memory.lost_relatives.length > 0 && (
                      <div style={{ background: 'rgba(245, 158, 11, 0.08)', padding: '8px 10px', borderRadius: '6px', fontSize: '11px', color: '#FCD34D' }}>
                        💔 <strong>Luto:</strong> Perda de {memory.lost_relatives.map((r) => r.name).join(', ')}
                      </div>
                    )}
                    {(!memory || (memory.danger_zones.length === 0 && memory.known_food_sources.length === 0 && memory.lost_relatives.length === 0)) && (
                      <div style={{ fontSize: '11px', color: '#64748B', textAlign: 'center', padding: '10px' }}>
                        Nenhuma experiência traumática ou marco geográfico gravado na memória recente.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: LINHAGEM & GENEALOGIA */}
            {activeTab === 'tree' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Progenitores */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Pais & Progenitores
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '6px' }}>
                    {renderRelativeCard('Pai', tree?.father)}
                    {renderRelativeCard('Mãe', tree?.mother)}
                  </div>
                </div>

                {/* Avós */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Avós Paternos & Maternos
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '6px' }}>
                    {renderRelativeCard('Avô Paterno', tree?.grandparents.paternal_grandfather)}
                    {renderRelativeCard('Avó Paterna', tree?.grandparents.paternal_grandmother)}
                    {renderRelativeCard('Avô Materno', tree?.grandparents.maternal_grandfather)}
                    {renderRelativeCard('Avó Materna', tree?.grandparents.maternal_grandmother)}
                  </div>
                </div>

                {/* Descendência / Filhotes */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                      Descendentes Diretos ({tree?.children.length ?? 0})
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                    {tree?.children && tree.children.length > 0 ? (
                      tree.children.map((child) => renderRelativeCard('Descendente', child, `Gen ${child.generation}`))
                    ) : (
                      <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', fontSize: '11px', color: 'var(--color-text-muted)', textAlign: 'center' }}>
                        Nenhum descendente gerado até o momento.
                      </div>
                    )}
                  </div>
                </div>

                {/* Mutações Sofridas no Nascimento */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8' }}>
                    Mutações no Nascimento ({animal?.mutations.length ?? 0})
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                    {animal?.mutations && animal.mutations.length > 0 ? (
                      animal.mutations.map((mut, idx) => (
                        <div
                          key={idx}
                          style={{
                            background: 'rgba(168, 85, 247, 0.08)',
                            border: '1px solid rgba(168, 85, 247, 0.25)',
                            padding: '8px 10px',
                            borderRadius: '6px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            fontSize: '11px',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Dna size={14} color="#C084FC" />
                            <strong style={{ color: '#F8FAFC', textTransform: 'capitalize' }}>{mut.attribute}</strong>
                          </div>
                          <span style={{ color: mut.delta > 0 ? '#34D399' : '#F87171', fontWeight: 700 }}>
                            {mut.delta > 0 ? `+${mut.delta.toFixed(1)}` : mut.delta.toFixed(1)} ({mut.category})
                          </span>
                        </div>
                      ))
                    ) : (
                      <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '8px', borderRadius: '6px', fontSize: '11px', color: '#64748B', textAlign: 'center' }}>
                        Nenhuma mutação detectada no nascimento (herança pura dos progenitores).
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
