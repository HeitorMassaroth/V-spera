/**
 * Motor de renderização em HTML5 Canvas 2D de alta performance.
 */

import type { CompactOrganism, CompactFood } from '../types';

export interface RenderOptions {
  showSensoryRadius: boolean;
  showVelocityVectors: boolean;
  showGridLines: boolean;
  worldWidth: number;
  worldHeight: number;
}

export class WorldRenderer {
  private ctx: CanvasRenderingContext2D;
  public scale: number = 1.0;
  public offsetX: number = 0.0;
  public offsetY: number = 0.0;

  constructor(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx;
  }

  public setContext(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx;
  }

  public resetView(canvasWidth: number, canvasHeight: number, worldWidth: number, worldHeight: number) {
    const scaleX = (canvasWidth - 60) / worldWidth;
    const scaleY = (canvasHeight - 60) / worldHeight;
    this.scale = Math.min(scaleX, scaleY, 1.2);
    this.offsetX = (canvasWidth - worldWidth * this.scale) / 2;
    this.offsetY = (canvasHeight - worldHeight * this.scale) / 2;
  }

  public render(
    organisms: CompactOrganism[],
    foods: CompactFood[],
    clusters: [number, number][],
    options: RenderOptions,
    canvasWidth: number,
    canvasHeight: number
  ) {
    const ctx = this.ctx;
    ctx.save();

    // Limpa fundo
    ctx.fillStyle = '#080C14';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Aplica transformações de câmera (Pan & Zoom)
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);

    // 1. Limites do ecossistema e grade espacial
    this.renderWorldBoundsAndGrid(ctx, options.worldWidth, options.worldHeight, options.showGridLines);

    // 2. Centros férteis / oásis de recursos
    this.renderFertileOases(ctx, clusters);

    // 3. Alimentos (pontos nutritivos com brilho)
    this.renderFoods(ctx, foods);

    // 4. Organismos vivos
    this.renderOrganisms(ctx, organisms, options);

    ctx.restore();
  }

  private renderFertileOases(ctx: CanvasRenderingContext2D, clusters: [number, number][]) {
    if (!clusters || clusters.length === 0) return;
    ctx.save();
    for (const [cx, cy] of clusters) {
      // Gradiente radial suave no miolo do centro de recursos
      const grad = ctx.createRadialGradient(cx, cy, 5, cx, cy, 90);
      grad.addColorStop(0, 'rgba(16, 185, 129, 0.12)');
      grad.addColorStop(0.5, 'rgba(16, 185, 129, 0.04)');
      grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

      ctx.beginPath();
      ctx.arc(cx, cy, 90, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Círculo sutil delimitador da zona
      ctx.beginPath();
      ctx.arc(cx, cy, 90, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(52, 211, 153, 0.18)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.restore();
  }

  private renderWorldBoundsAndGrid(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    showGrid: boolean
  ) {
    // Fundo do mundo virtual
    ctx.fillStyle = '#0B111E';
    ctx.fillRect(0, 0, w, h);

    // Grid sutil
    if (showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.035)';
      ctx.lineWidth = 1;
      const step = 60; // coincide com tamanho da célula do SpatialHashGrid
      ctx.beginPath();
      for (let x = 0; x <= w; x += step) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
      }
      for (let y = 0; y <= h; y += step) {
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
      }
      ctx.stroke();
    }

    // Borda iluminada com gradiente
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 2.5;
    ctx.strokeRect(0, 0, w, h);
  }

  private renderFoods(ctx: CanvasRenderingContext2D, foods: CompactFood[]) {
    ctx.save();
    for (const food of foods) {
      const [, fx, fy] = food;

      // Glow suave de alimento
      ctx.beginPath();
      ctx.arc(fx, fy, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(52, 211, 153, 0.25)';
      ctx.fill();

      // Núcleo brilhante
      ctx.beginPath();
      ctx.arc(fx, fy, 2.8, 0, Math.PI * 2);
      ctx.fillStyle = '#34D399';
      ctx.shadowColor = '#10B981';
      ctx.shadowBlur = 6;
      ctx.fill();
    }
    ctx.restore();
  }

  private renderOrganisms(
    ctx: CanvasRenderingContext2D,
    organisms: CompactOrganism[],
    options: RenderOptions
  ) {
    ctx.save();
    for (const org of organisms) {
      const heading = Math.atan2(org.vy, org.vx);
      const energyRatio = Math.max(0.1, Math.min(1.0, org.e / 100.0));

      // 1. Halo sensorial (raio de visão)
      if (options.showSensoryRadius) {
        ctx.beginPath();
        ctx.arc(org.x, org.y, 75, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      ctx.save();
      ctx.translate(org.x, org.y);
      ctx.rotate(heading);

      // Vetor de velocidade
      if (options.showVelocityVectors) {
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(org.sz * 2.5, 0);
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Corpo celular orgânico estilizado (elipse orientada na direção do vetor)
      ctx.beginPath();
      ctx.ellipse(0, 0, org.sz * 1.35, org.sz * 0.9, 0, 0, Math.PI * 2);

      // Cor HSL com saturação e luminosidade modulada pela reserva energética
      const lightness = 35 + energyRatio * 25; // 35% quando sem energia, 60% com energia cheia
      ctx.fillStyle = `hsl(${org.h}, 85%, ${lightness}%)`;
      ctx.shadowColor = `hsl(${org.h}, 90%, 50%)`;
      ctx.shadowBlur = energyRatio > 0.4 ? 8 : 2;
      ctx.fill();

      // Borda da membrana celular
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
      ctx.stroke();

      // Núcleo celular
      ctx.beginPath();
      ctx.arc(org.sz * 0.35, 0, org.sz * 0.38, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fill();

      ctx.restore();
    }
    ctx.restore();
  }
}
