import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Eye,
  Compass,
  Grid,
  Shield,
  Maximize2,
  Crosshair,
  MousePointer,
  Apple,
  Film,
} from 'lucide-react';
import type { CompactOrganism, CompactFood, AttributeStats, WorldEvent, NestInfo, ClanInfo, TerritoryZoneInfo, SeasonInfo } from '../types';
import { WorldRenderer, type RenderOptions } from '../canvas/WorldRenderer';
import { AnimalInspector } from './AnimalInspector';

interface SimulationViewerProps {
  organisms: CompactOrganism[];
  foods: CompactFood[];
  clusters: [number, number][];
  clusterHomes?: Record<number, number>;
  nests?: NestInfo[];
  clans?: ClanInfo[];
  territories?: TerritoryZoneInfo[];
  season?: SeasonInfo | null;
  populationAverages?: AttributeStats;
  events?: WorldEvent[];
  tick: number;
  worldWidth: number;
  worldHeight: number;
  selectedOrganismId: number | null;
  onSelectOrganism: (id: number | null) => void;
  onSpawnFood: (x: number, y: number) => void;
  onPlayPauseToggle: () => void;
  onStep: () => void;
  onReset: () => void;
  onSpeedChange: (tps: number) => void;
  tps: number;
}

export const SimulationViewer: React.FC<SimulationViewerProps> = ({
  organisms,
  foods,
  clusters,
  clusterHomes,
  nests,
  clans,
  territories,
  season,
  populationAverages,
  events,
  tick,
  worldWidth,
  worldHeight,
  selectedOrganismId,
  onSelectOrganism,
  onSpawnFood,
  onPlayPauseToggle,
  onStep,
  onReset,
  onSpeedChange,
  tps,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<WorldRenderer | null>(null);
  const dimensionsRef = useRef<{ width: number; height: number }>({ width: 800, height: 600 });

  // Modos de Ferramenta Interativa
  const [activeTool, setActiveTool] = useState<'inspect' | 'feed'>('inspect');
  const [followSelected, setFollowSelected] = useState<boolean>(false);
  const [cinematicMode, setCinematicMode] = useState<boolean>(false);
  const [cinematicLabel, setCinematicLabel] = useState<string>('');

  // Estados de visualização
  const [showSensoryRadius, setShowSensoryRadius] = useState<boolean>(false);
  const [showVelocityVectors, setShowVelocityVectors] = useState<boolean>(true);
  const [showGridLines, setShowGridLines] = useState<boolean>(true);
  const [showTerritories, setShowTerritories] = useState<boolean>(true);

  // Estados de Pan & Zoom
  const isDraggingRef = useRef<boolean>(false);
  const lastMousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const mouseDownPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Referência para as entidades mais recentes
  const stateRef = useRef({
    organisms,
    foods,
    clusters,
    clusterHomes,
    nests,
    clans,
    territories,
    season,
    worldWidth,
    worldHeight,
    events,
    tick,
  });
  useEffect(() => {
    stateRef.current = {
      organisms,
      foods,
      clusters,
      clusterHomes,
      nests,
      clans,
      territories,
      season,
      worldWidth,
      worldHeight,
      events,
      tick,
    };
  }, [organisms, foods, clusters, clusterHomes, nests, clans, territories, season, worldWidth, worldHeight, events, tick]);

  const selectedIdRef = useRef<number | null>(selectedOrganismId);
  useEffect(() => {
    selectedIdRef.current = selectedOrganismId;
  }, [selectedOrganismId]);

  const followSelectedRef = useRef<boolean>(followSelected);
  useEffect(() => {
    followSelectedRef.current = followSelected;
  }, [followSelected]);

  const cinematicModeRef = useRef<boolean>(cinematicMode);
  useEffect(() => {
    cinematicModeRef.current = cinematicMode;
  }, [cinematicMode]);
  const cinematicTargetRef = useRef<{ id: number; untilTick: number; reason: string } | null>(null);

  // Inicialização e Resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const renderer = new WorldRenderer(ctx);
    rendererRef.current = renderer;

    const handleResize = () => {
      if (!containerRef.current || !canvas) return;
      const rect = containerRef.current.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2.5);

      dimensionsRef.current = { width: rect.width, height: rect.height };

      canvas.width = Math.floor(rect.width * dpr);
      canvas.height = Math.floor(rect.height * dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;

      renderer.dpr = dpr;
      renderer.resetView(rect.width, rect.height, worldWidth, worldHeight);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Loop de renderização fluida 60 FPS com requestAnimationFrame
    let animationFrameId: number;
    const renderLoop = () => {
      if (rendererRef.current && canvas) {
        const { width: viewW, height: viewH } = dimensionsRef.current;

        // Modo Câmera de Cinema / Documentário Automático
        if (cinematicModeRef.current) {
          const currentTick = stateRef.current.tick;
          const liveOrgs = stateRef.current.organisms;

          let targetOrg = liveOrgs.find((o) => o.id === cinematicTargetRef.current?.id);

          if (!targetOrg || currentTick >= (cinematicTargetRef.current?.untilTick ?? 0)) {
            // 1. Prioridade: Evento dramático recente (combate, predação, reprodução)
            const recentEvent = stateRef.current.events?.slice(-10).reverse().find((e) => {
              const eOrgId = (e as any).organism_id || (e as any).predator_id || (e as any).subject_id;
              return eOrgId && liveOrgs.some((o) => o.id === eOrgId);
            });

            if (recentEvent) {
              const eventOrgId = (recentEvent as any).organism_id || (recentEvent as any).predator_id || (recentEvent as any).subject_id;
              targetOrg = liveOrgs.find((o) => o.id === eventOrgId);
              if (targetOrg) {
                cinematicTargetRef.current = {
                  id: targetOrg.id,
                  untilTick: currentTick + 150,
                  reason: `⚡ Ação: Animal #${targetOrg.id} (${recentEvent.type})`,
                };
              }
            }

            // 2. Prioridade: Líder Alpha de Clã ativo
            if (!targetOrg && stateRef.current.clans && stateRef.current.clans.length > 0) {
              const alphaClan = stateRef.current.clans.find((c) => c.alpha_id && liveOrgs.some((o) => o.id === c.alpha_id));
              if (alphaClan && alphaClan.alpha_id) {
                targetOrg = liveOrgs.find((o) => o.id === alphaClan.alpha_id);
                if (targetOrg) {
                  cinematicTargetRef.current = {
                    id: targetOrg.id,
                    untilTick: currentTick + 200,
                    reason: `👑 Líder Alpha #${targetOrg.id} (Clã ${alphaClan.name})`,
                  };
                }
              }
            }

            // 3. Prioridade: Espécime de maior destaque / energia
            if (!targetOrg && liveOrgs.length > 0) {
              const sorted = [...liveOrgs].sort((a, b) => b.e - a.e);
              targetOrg = sorted[0];
              if (targetOrg) {
                cinematicTargetRef.current = {
                  id: targetOrg.id,
                  untilTick: currentTick + 180,
                  reason: `🌟 Espécime #${targetOrg.id} (Gen ${targetOrg.gen || 0})`,
                };
              }
            }

            if (cinematicTargetRef.current) {
              setCinematicLabel(cinematicTargetRef.current.reason);
            }
          }

          if (targetOrg) {
            const targetOffsetX = viewW / 2 - targetOrg.x * rendererRef.current.scale;
            const targetOffsetY = viewH / 2 - targetOrg.y * rendererRef.current.scale;
            rendererRef.current.offsetX += (targetOffsetX - rendererRef.current.offsetX) * 0.08;
            rendererRef.current.offsetY += (targetOffsetY - rendererRef.current.offsetY) * 0.08;
          }
        } else if (followSelectedRef.current && selectedIdRef.current !== null) {
          const target = stateRef.current.organisms.find((o) => o.id === selectedIdRef.current);
          if (target) {
            const targetOffsetX = viewW / 2 - target.x * rendererRef.current.scale;
            const targetOffsetY = viewH / 2 - target.y * rendererRef.current.scale;
            // Interpolação suave (lerp)
            rendererRef.current.offsetX += (targetOffsetX - rendererRef.current.offsetX) * 0.12;
            rendererRef.current.offsetY += (targetOffsetY - rendererRef.current.offsetY) * 0.12;
          }
        }

        const options: RenderOptions = {
          showSensoryRadius,
          showVelocityVectors,
          showGridLines,
          showTerritories,
          worldWidth: stateRef.current.worldWidth,
          worldHeight: stateRef.current.worldHeight,
        };

        rendererRef.current.render(
          stateRef.current.organisms,
          stateRef.current.foods,
          stateRef.current.clusters,
          options,
          viewW,
          viewH,
          stateRef.current.clusterHomes,
          selectedIdRef.current,
          stateRef.current.events,
          stateRef.current.tick,
          stateRef.current.nests,
          stateRef.current.clans,
          stateRef.current.territories,
          stateRef.current.season
        );
      }
      animationFrameId = requestAnimationFrame(renderLoop);
    };

    animationFrameId = requestAnimationFrame(renderLoop);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, [showSensoryRadius, showVelocityVectors, showGridLines, showTerritories, worldWidth, worldHeight]);

  // Atalhos de teclado
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === 'Space') {
        e.preventDefault();
        onPlayPauseToggle();
      } else if (e.key === '.') {
        e.preventDefault();
        onStep();
      } else if (e.key.toLowerCase() === 'r') {
        e.preventDefault();
        onReset();
      } else if (e.key === 'Escape') {
        onSelectOrganism(null);
        setFollowSelected(false);
        setCinematicMode(false);
      } else if (e.key.toLowerCase() === 'c') {
        setCinematicMode((prev) => !prev);
      } else if (e.key.toLowerCase() === 'f') {
        setActiveTool((prev) => (prev === 'inspect' ? 'feed' : 'inspect'));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onPlayPauseToggle, onStep, onReset, onSelectOrganism]);

  // Manipuladores de mouse para Pan, Zoom e Ferramentas Interativas
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDraggingRef.current || !rendererRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    rendererRef.current.offsetX += dx;
    rendererRef.current.offsetY += dy;

    // Se o usuário arrastou a tela, desativa followSelected e cinematicMode temporariamente para dar controle manual
    if (Math.hypot(dx, dy) > 2) {
      setFollowSelected(false);
      setCinematicMode(false);
    }
  }, []);

  const handleMouseUp = useCallback(
    (e: React.MouseEvent) => {
      isDraggingRef.current = false;
      if (!canvasRef.current || !rendererRef.current) return;

      const dragDist = Math.hypot(
        e.clientX - mouseDownPosRef.current.x,
        e.clientY - mouseDownPosRef.current.y
      );

      // Clique no canvas (sem arrastar)
      if (dragDist < 5) {
        const rect = canvasRef.current.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;

        if (activeTool === 'feed') {
          // Modo Criador: Semear alimento interativamente
          const worldPos = rendererRef.current.screenToWorld(screenX, screenY);
          onSpawnFood(worldPos.x, worldPos.y);
        } else {
          // Modo Inspecionar
          const hit = rendererRef.current.getOrganismAt(
            screenX,
            screenY,
            stateRef.current.organisms
          );

          if (hit) {
            onSelectOrganism(hit.id);
          } else {
            onSelectOrganism(null);
            setFollowSelected(false);
          }
        }
      }
    },
    [activeTool, onSelectOrganism, onSpawnFood]
  );

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    if (!rendererRef.current || !canvasRef.current) return;

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const renderer = rendererRef.current;
    const newScale = Math.max(0.2, Math.min(4.0, renderer.scale * zoomFactor));

    renderer.offsetX = mouseX - (mouseX - renderer.offsetX) * (newScale / renderer.scale);
    renderer.offsetY = mouseY - (mouseY - renderer.offsetY) * (newScale / renderer.scale);
    renderer.scale = newScale;
  }, []);

  const handleResetView = useCallback(() => {
    if (!rendererRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    rendererRef.current.resetView(rect.width, rect.height, worldWidth, worldHeight);
    setFollowSelected(false);
  }, [worldWidth, worldHeight]);

  const liveSelectedOrganism = organisms.find((o) => o.id === selectedOrganismId);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: '#06090F',
      }}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          isDraggingRef.current = false;
        }}
        onWheel={handleWheel}
        style={{
          display: 'block',
          cursor: activeTool === 'feed' ? 'copy' : 'crosshair',
          width: '100%',
          height: '100%',
        }}
      />

      {/* Floating Toolbar Top-Left: Ferramentas Interativas e Camadas */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          display: 'flex',
          gap: '6px',
          padding: '6px 8px',
          borderRadius: '10px',
          zIndex: 10,
        }}
      >
        {/* Seletor de Ferramenta */}
        <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '6px', padding: '2px' }}>
          <button
            onClick={() => setActiveTool('inspect')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '5px',
              fontSize: '11px',
              fontWeight: 700,
              background: activeTool === 'inspect' ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
              color: activeTool === 'inspect' ? '#38BDF8' : 'var(--color-text-muted)',
              border: 'none',
              cursor: 'pointer',
            }}
            title="Clique nos animais para inspecionar atributos e genealogia"
          >
            <MousePointer size={12} /> Inspecionar
          </button>

          <button
            onClick={() => setActiveTool('feed')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '5px',
              fontSize: '11px',
              fontWeight: 700,
              background: activeTool === 'feed' ? 'rgba(52, 211, 153, 0.25)' : 'transparent',
              color: activeTool === 'feed' ? '#34D399' : 'var(--color-text-muted)',
              border: 'none',
              cursor: 'pointer',
            }}
            title="Clique no canvas para semear alimento (Isca de nutrientes)"
          >
            <Apple size={12} /> Semear Alimento
          </button>
        </div>

        <div style={{ width: '1px', background: 'rgba(255, 255, 255, 0.1)', margin: '0 2px' }} />

        {/* Camadas Visuais */}
        <button
          onClick={() => setShowSensoryRadius(!showSensoryRadius)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: showSensoryRadius ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
            color: showSensoryRadius ? '#38BDF8' : 'var(--color-text-muted)',
            border: `1px solid ${showSensoryRadius ? 'rgba(56, 189, 248, 0.4)' : 'transparent'}`,
            cursor: 'pointer',
          }}
          title="Alternar raio sensorial"
        >
          <Eye size={12} /> Visão
        </button>

        <button
          onClick={() => setShowVelocityVectors(!showVelocityVectors)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: showVelocityVectors ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
            color: showVelocityVectors ? '#F59E0B' : 'var(--color-text-muted)',
            border: `1px solid ${showVelocityVectors ? 'rgba(245, 158, 11, 0.4)' : 'transparent'}`,
            cursor: 'pointer',
          }}
          title="Alternar vetores de direção"
        >
          <Compass size={12} /> Vetores
        </button>

        <button
          onClick={() => setShowGridLines(!showGridLines)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: showGridLines ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
            color: showGridLines ? '#F1F5F9' : 'var(--color-text-muted)',
            border: `1px solid ${showGridLines ? 'rgba(255, 255, 255, 0.2)' : 'transparent'}`,
            cursor: 'pointer',
          }}
          title="Alternar grade espacial"
        >
          <Grid size={12} /> Grade
        </button>

        <button
          onClick={() => setShowTerritories(!showTerritories)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: showTerritories ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
            color: showTerritories ? '#34D399' : 'var(--color-text-muted)',
            border: `1px solid ${showTerritories ? 'rgba(16, 185, 129, 0.4)' : 'transparent'}`,
            cursor: 'pointer',
          }}
          title="Alternar visualização das regiões territoriais e indicadores de qualidade"
        >
          <Shield size={12} /> Territórios
        </button>
      </div>

      {/* Floating Caste & Division Legend Top-Right */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '16px',
          right: selectedOrganismId !== null ? '410px' : '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
          padding: '8px 12px',
          borderRadius: '10px',
          fontSize: '11px',
          pointerEvents: 'none',
          background: 'rgba(11, 17, 30, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          zIndex: 10,
          transition: 'right 0.2s ease',
        }}
      >
        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94A3B8' }}>
          Divisões Naturais
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#FB7185', display: 'inline-block' }} />
          <span style={{ color: '#FDA4AF' }}>Rosa (Fêmea)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34D399', display: 'inline-block' }} />
          <span style={{ color: '#6EE7B7' }}>Verde (Macho Guardião)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#C084FC', display: 'inline-block' }} />
          <span style={{ color: '#D8B4FE' }}>Roxo (Filhote)</span>
        </div>
      </div>

      {/* Painel Individual de Inspeção do Animal Selecionado */}
      {selectedOrganismId !== null && (
        <AnimalInspector
          organismId={selectedOrganismId}
          liveOrganism={liveSelectedOrganism}
          populationAverages={populationAverages}
          onClose={() => {
            onSelectOrganism(null);
            setFollowSelected(false);
          }}
          onSelectOrganism={(newId) => onSelectOrganism(newId)}
        />
      )}

      {/* Cinematic HUD Pill Top-Center */}
      {cinematicMode && (
        <div
          className="glass-panel"
          style={{
            position: 'absolute',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '999px',
            background: 'rgba(15, 23, 42, 0.88)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            boxShadow: '0 0 24px rgba(239, 68, 68, 0.25)',
            zIndex: 20,
            pointerEvents: 'none',
            backdropFilter: 'blur(8px)',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#EF4444',
              display: 'inline-block',
              boxShadow: '0 0 8px #EF4444',
            }}
          />
          <span style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.08em', color: '#FCA5A5', textTransform: 'uppercase' }}>
            VÉSPERA DOC &bull; CÂMERA CINEMA
          </span>
          {cinematicLabel && (
            <span style={{ fontSize: '11px', color: '#F1F5F9', borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '8px' }}>
              {cinematicLabel}
            </span>
          )}
        </div>
      )}

      {/* Floating Center View & Speed Buttons Bottom-Right */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          right: '16px',
          display: 'flex',
          gap: '8px',
          zIndex: 10,
        }}
      >
        <button
          onClick={() => {
            setCinematicMode(!cinematicMode);
            if (!cinematicMode) {
              setFollowSelected(false);
            }
          }}
          className="glass-panel"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '11px',
            fontWeight: 700,
            background: cinematicMode ? 'rgba(239, 68, 68, 0.25)' : 'rgba(15, 23, 42, 0.8)',
            color: cinematicMode ? '#F87171' : '#94A3B8',
            border: `1px solid ${cinematicMode ? '#EF4444' : 'rgba(255, 255, 255, 0.1)'}`,
            cursor: 'pointer',
          }}
          title="Ativar câmera automática de documentário natural (Atalho [C])"
        >
          <Film size={13} /> {cinematicMode ? 'Cinema Ativo' : 'Câmera Cinema'}
        </button>

        {selectedOrganismId !== null && (
          <button
            onClick={() => setFollowSelected(!followSelected)}
            className="glass-panel"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '8px 12px',
              borderRadius: '8px',
              fontSize: '11px',
              fontWeight: 700,
              background: followSelected ? 'rgba(56, 189, 248, 0.25)' : 'rgba(15, 23, 42, 0.8)',
              color: followSelected ? '#38BDF8' : '#94A3B8',
              border: `1px solid ${followSelected ? '#38BDF8' : 'rgba(255, 255, 255, 0.1)'}`,
              cursor: 'pointer',
            }}
            title="Travar câmera e seguir animal selecionado em tempo real"
          >
            <Crosshair size={13} /> {followSelected ? 'Seguindo' : 'Seguir Animal'}
          </button>
        )}

        <div
          className="glass-panel"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            padding: '3px 6px',
            borderRadius: '8px',
          }}
        >
          {[15, 30, 60].map((speed) => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed)}
              style={{
                padding: '4px 7px',
                borderRadius: '5px',
                fontSize: '10px',
                fontWeight: 700,
                border: 'none',
                background: tps === speed ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                color: tps === speed ? '#38BDF8' : 'var(--color-text-muted)',
                cursor: 'pointer',
              }}
              title={`Definir velocidade para ${speed} TPS`}
            >
              {speed} TPS
            </button>
          ))}
        </div>

        <button
          onClick={handleResetView}
          className="glass-panel"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '11px',
            fontWeight: 600,
            color: '#38BDF8',
            cursor: 'pointer',
          }}
          title="Centralizar e ajustar mundo na tela"
        >
          <Maximize2 size={13} /> Centralizar
        </button>
      </div>

      {/* Bottom Shortcuts Hint & Quick Mode */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          fontSize: '11px',
          color: 'rgba(255, 255, 255, 0.5)',
          background: 'rgba(0, 0, 0, 0.55)',
          padding: '5px 12px',
          borderRadius: '6px',
          pointerEvents: 'none',
          zIndex: 10,
          backdropFilter: 'blur(8px)',
        }}
      >
        {activeTool === 'feed' ? (
          <span style={{ color: '#34D399', fontWeight: 600 }}>
            🌿 Clique em qualquer ponto do canvas para semear alimento!
          </span>
        ) : (
          <span>
            💡 <b>Clique em qualquer habitante</b> para inspecionar &bull; Atalho <span style={{ color: '#E2E8F0' }}>[C]</span> Câmera Cinema &bull;{' '}
            <span style={{ color: '#E2E8F0' }}>[F]</span> Semear Alimento &bull; <span style={{ color: '#E2E8F0' }}>[Espaço]</span> Iniciar/Pausar
          </span>
        )}
      </div>
    </div>
  );
};
