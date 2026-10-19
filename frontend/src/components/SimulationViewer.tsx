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

  // Modos de Ferramenta Interativa
  const [activeTool, setActiveTool] = useState<'inspect' | 'feed'>('inspect');
  const [followSelected, setFollowSelected] = useState<boolean>(false);

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
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;

      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);

      renderer.resetView(rect.width, rect.height, worldWidth, worldHeight);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Loop de renderização fluida 60 FPS com requestAnimationFrame
    let animationFrameId: number;
    const renderLoop = () => {
      if (rendererRef.current && canvas) {
        const rect = canvas.getBoundingClientRect();

        // Modo Seguir Habitante Selecionado
        if (followSelectedRef.current && selectedIdRef.current !== null) {
          const target = stateRef.current.organisms.find((o) => o.id === selectedIdRef.current);
          if (target) {
            const targetOffsetX = rect.width / 2 - target.x * rendererRef.current.scale;
            const targetOffsetY = rect.height / 2 - target.y * rendererRef.current.scale;
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
          rect.width,
          rect.height,
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

    // Se o usuário arrastou a tela, desativa followSelected temporariamente para dar controle manual
    if (Math.hypot(dx, dy) > 2) {
      setFollowSelected(false);
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
            💡 <b>Clique em qualquer habitante</b> para inspecionar &bull; Atalho <span style={{ color: '#E2E8F0' }}>[F]</span> Semear Alimento &bull;{' '}
            <span style={{ color: '#E2E8F0' }}>[Espaço]</span> Iniciar/Pausar
          </span>
        )}
      </div>
    </div>
  );
};
