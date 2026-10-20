import React, { useState, useEffect, useCallback } from 'react';
import { X, GitBranch, RefreshCw, Filter, User } from 'lucide-react';

interface PhylogenyNode {
  id: number;
  name: string;
  generation: number;
  species: string;
  sex: string;
  alive: boolean;
  birth_tick: number;
  death_tick?: number;
  father_id?: number;
  mother_id?: number;
  inbreeding_coefficient: number;
  lineage_id: string | number;
  lineage_name: string;
  forca: number;
  velocidade: number;
  resistencia: number;
  coleta: number;
  children_count: number;
}

interface PhylogenyLink {
  source: number;
  target: number;
  relationship: 'father' | 'mother';
}

interface LineageSummary {
  name: string;
  total_descendants: number;
  alive_count: number;
  founders: number[];
}

interface PhylogenyData {
  total_nodes: number;
  total_links: number;
  max_generation: number;
  nodes: PhylogenyNode[];
  links: PhylogenyLink[];
  lineages: LineageSummary[];
}

interface PhylogenyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectOrganism: (id: number) => void;
}

export const PhylogenyModal: React.FC<PhylogenyModalProps> = ({
  isOpen,
  onClose,
  onSelectOrganism,
}) => {
  const [data, setData] = useState<PhylogenyData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedLineage, setSelectedLineage] = useState<string>('all');
  const [selectedSpecies, setSelectedSpecies] = useState<string>('all');
  const [onlyLiving, setOnlyLiving] = useState<boolean>(false);
  const [inspectNode, setInspectNode] = useState<PhylogenyNode | null>(null);

  const fetchPhylogeny = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/analytics/phylogeny');
      if (res.ok) {
        const json: PhylogenyData = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error('Falha ao carregar filogenia:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchPhylogeny();
      setInspectNode(null);
    }
  }, [isOpen, fetchPhylogeny]);

  if (!isOpen) return null;

  const filteredNodes = data?.nodes.filter((node) => {
    if (selectedLineage !== 'all' && node.lineage_name !== selectedLineage) return false;
    if (selectedSpecies !== 'all' && node.species !== selectedSpecies) return false;
    if (onlyLiving && !node.alive) return false;
    return true;
  }) || [];

  // Agrupamento por geração para renderização em colunas filogenéticas
  const generationGroups: Record<number, PhylogenyNode[]> = {};
  for (const node of filteredNodes) {
    if (!generationGroups[node.generation]) {
      generationGroups[node.generation] = [];
    }
    generationGroups[node.generation].push(node);
  }

  const generations = Object.keys(generationGroups)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '90vw',
          maxWidth: '1100px',
          height: '85vh',
          backgroundColor: '#0A0F1D',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          borderRadius: '12px',
          boxShadow: '0 25px 50px rgba(0, 0, 0, 0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.95)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(168, 85, 247, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#C084FC',
              }}
            >
              <GitBranch size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
                Árvore Filogenética & Genealogia Interativa
              </h3>
              <p style={{ fontSize: '11px', color: '#94A3B8', margin: 0 }}>
                Rastreamento de linhagens fundadoras (G0), consanguinidade de Wright e especiação
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={fetchPhylogeny}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#E2E8F0',
                fontSize: '12px',
                padding: '6px 10px',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <RefreshCw size={12} /> Atualizar
            </button>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Barra de Filtros */}
        <div
          style={{
            padding: '10px 24px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            fontSize: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8' }}>
            <Filter size={14} /> Filtros:
          </div>

          {/* Filtro por Linhagem */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#64748B' }}>Linhagem:</span>
            <select
              value={selectedLineage}
              onChange={(e) => setSelectedLineage(e.target.value)}
              style={{
                background: 'rgba(10, 15, 26, 0.9)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#F8FAFC',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
              }}
            >
              <option value="all">Todas as Linhagens</option>
              {data?.lineages.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name} ({l.alive_count} vivos / {l.total_descendants} total)
                </option>
              ))}
            </select>
          </div>

          {/* Filtro por Espécie */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#64748B' }}>Espécie:</span>
            <select
              value={selectedSpecies}
              onChange={(e) => setSelectedSpecies(e.target.value)}
              style={{
                background: 'rgba(10, 15, 26, 0.9)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#F8FAFC',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
              }}
            >
              <option value="all">Todas as Espécies</option>
              <option value="PREDATOR">Predadores (Lobos)</option>
              <option value="VRANCO">Vrancos (Aves)</option>
            </select>
          </div>

          {/* Toggle Apenas Vivos */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#E2E8F0' }}>
            <input
              type="checkbox"
              checked={onlyLiving}
              onChange={(e) => setOnlyLiving(e.target.checked)}
              style={{ accentColor: '#C084FC' }}
            />
            <span>Apenas Vivos</span>
          </label>

          <div style={{ marginLeft: 'auto', color: '#94A3B8', fontSize: '11px' }}>
            Exibindo {filteredNodes.length} de {data?.total_nodes ?? 0} registros genealógicos
          </div>
        </div>

        {/* Conteúdo Principal: Visualização de Gerações */}
        <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
          {/* Colunas Filogenéticas */}
          <div
            style={{
              flex: 1,
              overflowX: 'auto',
              overflowY: 'auto',
              padding: '20px 24px',
              display: 'flex',
              gap: '24px',
            }}
          >
            {loading ? (
              <div style={{ margin: 'auto', color: '#64748B', fontSize: '13px' }}>
                Construindo grafo genealógico...
              </div>
            ) : generations.length === 0 ? (
              <div style={{ margin: 'auto', color: '#64748B', fontSize: '13px' }}>
                Nenhum animal correspondente aos filtros ativos.
              </div>
            ) : (
              generations.map((gen) => (
                <div
                  key={gen}
                  style={{
                    minWidth: '220px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  {/* Cabeçalho da Geração */}
                  <div
                    style={{
                      background: 'rgba(30, 41, 59, 0.7)',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ fontSize: '12px', fontWeight: 800, color: '#C084FC' }}>
                      {gen === 0 ? 'G0 · Pioneiros' : `Geração ${gen}`}
                    </span>
                    <span style={{ fontSize: '10px', color: '#94A3B8' }}>
                      {generationGroups[gen].length} indiv.
                    </span>
                  </div>

                  {/* Cards dos Animais na Geração */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {generationGroups[gen].map((node) => {
                      const isSelected = inspectNode?.id === node.id;
                      const isVranco = node.species === 'VRANCO';

                      return (
                        <div
                          key={node.id}
                          onClick={() => setInspectNode(node)}
                          style={{
                            background: isSelected
                              ? 'rgba(168, 85, 247, 0.25)'
                              : node.alive
                              ? 'rgba(15, 23, 42, 0.85)'
                              : 'rgba(15, 23, 42, 0.45)',
                            border: `1px solid ${
                              isSelected
                                ? '#C084FC'
                                : node.alive
                                ? isVranco
                                  ? 'rgba(245, 158, 11, 0.4)'
                                  : 'rgba(56, 189, 248, 0.4)'
                                : 'rgba(255, 255, 255, 0.05)'
                            }`,
                            borderRadius: '8px',
                            padding: '10px 12px',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: node.alive ? '#F8FAFC' : '#94A3B8' }}>
                              {node.name}
                            </span>
                            <span
                              style={{
                                fontSize: '9px',
                                padding: '1px 5px',
                                borderRadius: '4px',
                                background: node.alive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                color: node.alive ? '#34D399' : '#FCA5A5',
                                fontWeight: 700,
                              }}
                            >
                              {node.alive ? 'VIVO' : 'FALECIDO'}
                            </span>
                          </div>

                          <div style={{ fontSize: '9px', color: '#94A3B8', marginTop: '3px' }}>
                            {isVranco ? '⚡ Vranco' : '🐺 Predador'} ({node.sex}) &bull; Linhagem {node.lineage_name}
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '9px', color: '#64748B' }}>
                            <span>F={node.forca.toFixed(0)} V={node.velocidade.toFixed(1)}</span>
                            {node.inbreeding_coefficient > 0 && (
                              <span style={{ color: node.inbreeding_coefficient > 0.05 ? '#F87171' : '#FBBF24' }}>
                                F={(node.inbreeding_coefficient).toFixed(3)}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Painel Lateral de Inspeção do Indivíduo */}
          {inspectNode && (
            <div
              style={{
                width: '320px',
                borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                background: 'rgba(15, 23, 42, 0.95)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                overflowY: 'auto',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#C084FC', textTransform: 'uppercase' }}>
                  Ficha do Habitante
                </span>
                <button
                  onClick={() => setInspectNode(null)}
                  style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
                >
                  <X size={15} />
                </button>
              </div>

              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
                  {inspectNode.name} #{inspectNode.id}
                </h4>
                <p style={{ fontSize: '11px', color: '#94A3B8', margin: '2px 0 0 0' }}>
                  Linhagem Fundadora: <strong>{inspectNode.lineage_name}</strong>
                </p>
              </div>

              {/* Status Biológico */}
              <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '10px', borderRadius: '6px', fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Espécie:</span>
                  <span style={{ color: '#F8FAFC' }}>{inspectNode.species} ({inspectNode.sex === 'F' ? 'Fêmea' : 'Macho'})</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Geração:</span>
                  <span style={{ color: '#C084FC', fontWeight: 700 }}>G{inspectNode.generation}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Ciclo de Vida:</span>
                  <span style={{ color: inspectNode.alive ? '#34D399' : '#FCA5A5' }}>
                    {inspectNode.alive ? `Nascido no tick #${inspectNode.birth_tick}` : `Faleceu no tick #${inspectNode.death_tick}`}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Consanguinidade (Wright):</span>
                  <span style={{ color: inspectNode.inbreeding_coefficient > 0.05 ? '#F87171' : '#34D399', fontWeight: 700 }}>
                    F = {inspectNode.inbreeding_coefficient.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Ascendência Direta */}
              <div style={{ fontSize: '11px' }}>
                <div style={{ color: '#94A3B8', fontWeight: 700, marginBottom: '6px' }}>
                  Pais Biológicos:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '6px 8px', borderRadius: '4px', color: '#7DD3FC' }}>
                    Pai: {inspectNode.father_id ? `#${inspectNode.father_id}` : 'Ancestral Fundador (G0)'}
                  </div>
                  <div style={{ background: 'rgba(251, 113, 133, 0.1)', padding: '6px 8px', borderRadius: '4px', color: '#FDA4AF' }}>
                    Mãe: {inspectNode.mother_id ? `#${inspectNode.mother_id}` : 'Ancestral Fundadora (G0)'}
                  </div>
                </div>
              </div>

              {/* Atributos Fenotípicos */}
              <div style={{ fontSize: '11px' }}>
                <div style={{ color: '#94A3B8', fontWeight: 700, marginBottom: '6px' }}>
                  Fenótipo Expresso:
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', textAlign: 'center', fontSize: '10px' }}>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px', borderRadius: '4px' }}>
                    <div style={{ color: '#94A3B8' }}>Força</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#F59E0B' }}>{inspectNode.forca}</div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px', borderRadius: '4px' }}>
                    <div style={{ color: '#94A3B8' }}>Velocidade</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#38BDF8' }}>{inspectNode.velocidade}</div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px', borderRadius: '4px' }}>
                    <div style={{ color: '#94A3B8' }}>Resistência</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#34D399' }}>{inspectNode.resistencia}</div>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px', borderRadius: '4px' }}>
                    <div style={{ color: '#94A3B8' }}>Coleta</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#C084FC' }}>{inspectNode.coleta}</div>
                  </div>
                </div>
              </div>

              {/* Botão de Rastrear no Canvas */}
              {inspectNode.alive && (
                <button
                  onClick={() => {
                    onSelectOrganism(inspectNode.id);
                    onClose();
                  }}
                  style={{
                    marginTop: 'auto',
                    padding: '8px',
                    borderRadius: '6px',
                    background: 'rgba(56, 189, 248, 0.2)',
                    border: '1px solid rgba(56, 189, 248, 0.4)',
                    color: '#38BDF8',
                    fontWeight: 700,
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <User size={13} /> Rastrear na Câmera
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
