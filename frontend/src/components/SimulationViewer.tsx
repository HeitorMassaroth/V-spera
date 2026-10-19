import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Eye, Compass, Grid, Maximize2 } from 'lucide-react';
import type { CompactOrganism, CompactFood } from '../types';
import { WorldRenderer, type RenderOptions } from '../canvas/WorldRenderer';

interface SimulationViewerProps {
  organisms: CompactOrganism[];
  foods: CompactFood[];
  worldWidth: number;
  worldHeight: number;
  onPlayPauseToggle: () => void;
  onStep: () => void;
  onReset: () => void;
}

export const SimulationViewer: React.FC<SimulationViewerProps> = ({
  organisms,
  foods,
  worldWidth,
  worldHeight,
  onPlayPauseToggle,
  onStep,
  onReset,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<WorldRenderer | null>(null);

  // Estados de visualização
  const [showSensoryRadius, setShowSensoryRadius] = useState<boolean>(false);
  const [showVelocityVectors, setShowVelocityVectors] = useState<boolean>(true);
  const [showGridLines, setShowGridLines] = useState<boolean>(true);

  // Estados de Pan & Zoom
  const isDraggingRef = useRef<boolean>(false);
  const lastMousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Referência para as entidades mais recentes
  const stateRef = useRef({ organisms, foods, worldWidth, worldHeight });
  useEffect(() => {
    stateRef.current = { organisms, foods, worldWidth, worldHeight };
  }, [organisms, foods, worldWidth, worldHeight]);

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
        const options: RenderOptions = {
          showSensoryRadius,
          showVelocityVectors,
          showGridLines,
          worldWidth: stateRef.current.worldWidth,
          worldHeight: stateRef.current.worldHeight,
        };

        rendererRef.current.render(
          stateRef.current.organisms,
          stateRef.current.foods,
          options,
          rect.width,
          rect.height
        );
      }
      animationFrameId = requestAnimationFrame(renderLoop);
    };

    animationFrameId = requestAnimationFrame(renderLoop);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, [showSensoryRadius, showVelocityVectors, showGridLines, worldWidth, worldHeight]);

  // Atalhos de teclado
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignora atalhos se o foco estiver num input
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
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onPlayPauseToggle, onStep, onReset]);

  // Manipuladores de mouse para Pan & Zoom
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDraggingRef.current || !rendererRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    rendererRef.current.offsetX += dx;
    rendererRef.current.offsetY += dy;
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    if (!rendererRef.current || !canvasRef.current) return;

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const renderer = rendererRef.current;
    const newScale = Math.max(0.2, Math.min(4.0, renderer.scale * zoomFactor));

    // Ajusta o offset para dar zoom centrado no ponteiro do mouse
    renderer.offsetX = mouseX - (mouseX - renderer.offsetX) * (newScale / renderer.scale);
    renderer.offsetY = mouseY - (mouseY - renderer.offsetY) * (newScale / renderer.scale);
    renderer.scale = newScale;
  }, []);

  const handleResetView = useCallback(() => {
    if (!rendererRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    rendererRef.current.resetView(rect.width, rect.height, worldWidth, worldHeight);
  }, [worldWidth, worldHeight]);

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
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{
          display: 'block',
          cursor: 'grab',
          width: '100%',
          height: '100%',
        }}
      />

      {/* Floating Toggles Top-Left */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          display: 'flex',
          gap: '8px',
          padding: '6px 10px',
          borderRadius: '10px',
        }}
      >
        <button
          onClick={() => setShowSensoryRadius(!showSensoryRadius)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: showSensoryRadius ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
            color: showSensoryRadius ? '#38BDF8' : 'var(--color-text-muted)',
            border: `1px solid ${showSensoryRadius ? 'rgba(56, 189, 248, 0.4)' : 'transparent'}`,
            cursor: 'pointer',
          }}
          title="Alternar visualização do raio sensorial"
        >
          <Eye size={13} /> Visão
        </button>

        <button
          onClick={() => setShowVelocityVectors(!showVelocityVectors)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 8px',
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
          <Compass size={13} /> Vetores
        </button>

        <button
          onClick={() => setShowGridLines(!showGridLines)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 8px',
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
          <Grid size={13} /> Grade
        </button>
      </div>

      {/* Floating Center View Button Bottom-Right */}
      <button
        onClick={handleResetView}
        className="glass-panel"
        style={{
          position: 'absolute',
          bottom: '16px',
          right: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '12px',
          fontWeight: 600,
          color: '#38BDF8',
          cursor: 'pointer',
        }}
        title="Centralizar e ajustar mundo na tela"
      >
        <Maximize2 size={14} /> Centralizar Visão
      </button>

      {/* Bottom Shortcuts Hint */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          fontSize: '11px',
          color: 'rgba(255, 255, 255, 0.4)',
          background: 'rgba(0, 0, 0, 0.5)',
          padding: '4px 10px',
          borderRadius: '6px',
          pointerEvents: 'none',
        }}
      >
        Atalhos: <span style={{ color: '#E2E8F0' }}>[Espaço]</span> Iniciar/Pausar &bull;{' '}
        <span style={{ color: '#E2E8F0' }}>[ . ]</span> Passo &bull;{' '}
        <span style={{ color: '#E2E8F0' }}>[R]</span> Reiniciar &bull; Arrasta / Scroll para Zoom
      </div>
    </div>
  );
};
