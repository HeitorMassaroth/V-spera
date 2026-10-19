/**
 * Motor de renderização em HTML5 Canvas 2D de alta performance.
 * Visualização da simulação VÉSPERA: Organismos simplificados, combate dinâmico e oásis de clãs.
 */

import type { CompactOrganism, CompactFood, WorldEvent, NestInfo, ClanInfo } from '../types';
import { getClanName } from '../types';

export interface RenderOptions {
  showSensoryRadius: boolean;
  showVelocityVectors: boolean;
  showGridLines: boolean;
  worldWidth: number;
  worldHeight: number;
}

interface VisualSpark {
  x: number;
  y: number;
  text?: string;
  color: string;
  life: number;
  maxLife: number;
  type: 'combat' | 'care' | 'clan';
}

export class WorldRenderer {
  private ctx: CanvasRenderingContext2D;
  public scale: number = 1.0;
  public offsetX: number = 0.0;
  public offsetY: number = 0.0;
  private sparks: VisualSpark[] = [];
  private lastProcessedTick: number = 0;

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

  /** Converte coordenadas de tela (pixel do canvas) para coordenadas do mundo */
  public screenToWorld(screenX: number, screenY: number): { x: number; y: number } {
    return {
      x: (screenX - this.offsetX) / this.scale,
      y: (screenY - this.offsetY) / this.scale,
    };
  }

  /** Centraliza a visão do mundo em um ponto ou animal específico */
  public centerOn(worldX: number, worldY: number, canvasWidth: number, canvasHeight: number) {
    this.offsetX = canvasWidth / 2 - worldX * this.scale;
    this.offsetY = canvasHeight / 2 - worldY * this.scale;
  }

  /** Localiza o organismo mais próximo de um ponto de clique */
  public getOrganismAt(screenX: number, screenY: number, organisms: CompactOrganism[]): CompactOrganism | null {
    const { x: wx, y: wy } = this.screenToWorld(screenX, screenY);
    let closest: CompactOrganism | null = null;
    let minDist = Infinity;

    for (const org of organisms) {
      const dx = org.x - wx;
      const dy = org.y - wy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const hitRadius = Math.max(org.sz + 6, 12);
      if (dist <= hitRadius && dist < minDist) {
        minDist = dist;
        closest = org;
      }
    }
    return closest;
  }

  /** Processa novos eventos do mundo para criar efeitos visuais de combate e carinho */
  public ingestEvents(events: WorldEvent[] | undefined, currentTick: number) {
    if (!events || events.length === 0) return;
    for (const ev of events) {
      if (ev.tick > this.lastProcessedTick) {
        if (ev.type === 'combat' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `-${ev.damage?.toFixed(1) || 'hit'}`,
            color: '#F87171',
            life: 28,
            maxLife: 28,
            type: 'combat',
          });
        } else if (ev.type === 'care' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: '+12 kcal',
            color: '#34D399',
            life: 28,
            maxLife: 28,
            type: 'care',
          });
        } else if (ev.type === 'pair_bonded' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: '💍 Vínculo',
            color: '#FDA4AF',
            life: 35,
            maxLife: 35,
            type: 'care',
          });
        } else if (ev.type === 'predation_kill' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: '💀 Predação',
            color: '#EF4444',
            life: 35,
            maxLife: 35,
            type: 'combat',
          });
        } else if (ev.type === 'mother_defense' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: '🛡️ Mãe Defende',
            color: '#FDA4AF',
            life: 30,
            maxLife: 30,
            type: 'combat',
          });
        } else if (ev.type === 'clan_formed' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `🏰 ${ev.message || 'Clã Formado'}`,
            color: '#A78BFA',
            life: 45,
            maxLife: 45,
            type: 'clan',
          });
        } else if (ev.type === 'alpha_elected' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `👑 ${ev.message || 'Alpha Eleito'}`,
            color: '#FBBF24',
            life: 45,
            maxLife: 45,
            type: 'clan',
          });
        } else if (ev.type === 'beta_elected' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `⭐ ${ev.message || 'Beta Eleito'}`,
            color: '#93C5FD',
            life: 40,
            maxLife: 40,
            type: 'clan',
          });
        } else if (ev.type === 'clan_war_declared' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `⚔️ ${ev.message || 'Guerra Declarada!'}`,
            color: '#EF4444',
            life: 50,
            maxLife: 50,
            type: 'combat',
          });
        } else if (ev.type === 'clan_truce_agreed' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `🕊️ ${ev.message || 'Trégua Firmada'}`,
            color: '#6EE7B7',
            life: 45,
            maxLife: 45,
            type: 'clan',
          });
        } else if (ev.type === 'family_expelled' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `🚫 ${ev.message || 'Família Expulsa'}`,
            color: '#FB923C',
            life: 45,
            maxLife: 45,
            type: 'clan',
          });
        }
      }
    }
    this.lastProcessedTick = currentTick;
  }

  public render(
    organisms: CompactOrganism[],
    foods: CompactFood[],
    clusters: [number, number][],
    options: RenderOptions,
    canvasWidth: number,
    canvasHeight: number,
    clusterHomes?: Record<number, number>,
    selectedId?: number | null,
    events?: WorldEvent[],
    currentTick: number = 0,
    nests?: NestInfo[],
    clans?: ClanInfo[]
  ) {
    const ctx = this.ctx;
    ctx.save();

    this.ingestEvents(events, currentTick);

    // Limpa fundo
    ctx.fillStyle = '#080C14';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Aplica transformações de câmera (Pan & Zoom)
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);

    // 1. Limites do ecossistema e grade espacial
    this.renderWorldBoundsAndGrid(ctx, options.worldWidth, options.worldHeight, options.showGridLines);

    // 2. Territórios Estratégicos de Clãs e Alianças Coletivas
    this.renderClanTerritories(ctx, clans, currentTick);

    // 2.1 Centros férteis / oásis de recursos
    this.renderFertileOases(ctx, clusters, clusterHomes);

    // 2.5 Ninhos Familiares e Berçários
    this.renderNests(ctx, nests);

    // 3. Alimentos (pontos nutritivos com brilho)
    this.renderFoods(ctx, foods);

    // 4. Organismos vivos simplificados e elegantes (Rosa, Verde, Roxo) com líderes Alpha e Beta
    this.renderOrganisms(ctx, organisms, options, selectedId, currentTick);

    // 5. Efeitos visuais de combate e cuidado parental
    this.renderSparks(ctx);

    ctx.restore();
  }

  private renderNests(ctx: CanvasRenderingContext2D, nests?: NestInfo[]) {
    if (!nests || nests.length === 0) return;
    ctx.save();

    for (const nest of nests) {
      if (!nest.is_active) continue;

      // Halo circular dourado suave do ninho
      const grad = ctx.createRadialGradient(nest.x, nest.y, 4, nest.x, nest.y, 32);
      grad.addColorStop(0, 'rgba(245, 158, 11, 0.25)');
      grad.addColorStop(0.5, 'rgba(251, 191, 36, 0.08)');
      grad.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

      ctx.beginPath();
      ctx.arc(nest.x, nest.y, 30, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Anel trançado do ninho
      ctx.beginPath();
      ctx.arc(nest.x, nest.y, 20, 0, Math.PI * 2);
      ctx.strokeStyle = nest.level === 3 ? '#F59E0B' : nest.level === 2 ? '#34D399' : 'rgba(251, 191, 36, 0.6)';
      ctx.lineWidth = 1.8;
      ctx.setLineDash([5, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Núcleo central do ninho
      ctx.beginPath();
      ctx.arc(nest.x, nest.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(251, 191, 36, 0.4)';
      ctx.fill();

      // Tag sobre o ninho com clã e estoque
      ctx.save();
      ctx.font = 'bold 9px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';
      const clanName = getClanName(nest.family_id);
      const tagText = `🪹 ${clanName} • 🌿${nest.food_storage.toFixed(0)}`;
      const textWidth = ctx.measureText(tagText).width;

      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.beginPath();
      ctx.roundRect(nest.x - textWidth / 2 - 5, nest.y - 34, textWidth + 10, 14, 4);
      ctx.fill();
      ctx.strokeStyle = 'rgba(251, 191, 36, 0.4)';
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.fillStyle = '#FDE68A';
      ctx.fillText(tagText, nest.x, nest.y - 25);
      ctx.restore();
    }

    ctx.restore();
  }

  /**
   * Renderiza os Territórios Dinâmicos dos Clãs, Estágios Sociais e Situações de Guerra/Paz
   */
  private renderClanTerritories(
    ctx: CanvasRenderingContext2D,
    clans?: ClanInfo[],
    currentTick: number = 0
  ) {
    if (!clans || clans.length === 0) return;
    ctx.save();

    for (const clan of clans) {
      const cx = clan.territory_center ? clan.territory_center[0] : clan.territory ? clan.territory.x : null;
      const cy = clan.territory_center ? clan.territory_center[1] : clan.territory ? clan.territory.y : null;
      if (cx === null || cy === null) continue;
      const baseRadius = clan.territory_radius || clan.territory?.radius || 120;

      // Verifica se está em guerra ativa
      const relations = clan.relations || clan.diplomacy || {};
      const isAtWar = Object.values(relations).includes('WAR');
      const pulse = isAtWar ? Math.sin(currentTick * 0.15) * 6 : 0;
      const radius = baseRadius + pulse;

      // Configuração visual por estágio social e estado bélico
      let strokeColor = 'rgba(56, 189, 248, 0.4)';
      let fillColorStart = 'rgba(56, 189, 248, 0.08)';
      let badgeBg = 'rgba(11, 17, 30, 0.9)';
      let stageLabel = 'Cooperação';

      if (clan.stage === 'ESTABLISHED_CLAN') {
        if (isAtWar) {
          strokeColor = 'rgba(239, 68, 68, 0.85)';
          fillColorStart = 'rgba(239, 68, 68, 0.14)';
          badgeBg = 'rgba(69, 10, 10, 0.92)';
          stageLabel = '⚔️ GUERRA';
        } else {
          strokeColor = 'rgba(245, 158, 11, 0.65)';
          fillColorStart = 'rgba(245, 158, 11, 0.10)';
          badgeBg = 'rgba(30, 20, 10, 0.92)';
          stageLabel = '🏰 Clã Estabelecido';
        }
      } else if (clan.stage === 'RECURRENT_COOP') {
        strokeColor = 'rgba(168, 85, 247, 0.55)';
        fillColorStart = 'rgba(168, 85, 247, 0.08)';
        stageLabel = 'Coop. Recorrente';
      } else if (clan.stage === 'OCCASIONAL_COOP') {
        strokeColor = 'rgba(56, 189, 248, 0.4)';
        fillColorStart = 'rgba(56, 189, 248, 0.06)';
        stageLabel = 'Coop. Ocasional';
      }

      // 1. Halo expansivo do Território
      const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radius);
      grad.addColorStop(0, fillColorStart);
      grad.addColorStop(0.75, fillColorStart);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // 2. Fronteira bioluminescente
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = isAtWar ? 2.5 : 1.8;
      ctx.setLineDash(isAtWar ? [6, 4] : [10, 6]);
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Estandarte Estratégico do Clã
      ctx.save();
      ctx.font = 'bold 10px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const memberCount = clan.member_organism_ids ? clan.member_organism_ids.length : (clan.family_ids ? clan.family_ids.length * 3 : 0);
      const titleText = `🏰 ${clan.name} [${stageLabel}]`;
      const subtitleText = `👑 #${clan.alpha_id ?? '?'} • ⭐ #${clan.beta_id ?? '?'} • 🥩 ${clan.communal_food.toFixed(0)} kcal • 👥 ${memberCount}`;

      const titleWidth = ctx.measureText(titleText).width;
      ctx.font = '9px system-ui, -apple-system, sans-serif';
      const subWidth = ctx.measureText(subtitleText).width;
      const boxWidth = Math.max(titleWidth, subWidth) + 24;

      const badgeY = cy - radius - 24;

      ctx.fillStyle = badgeBg;
      ctx.beginPath();
      ctx.roundRect(cx - boxWidth / 2, badgeY, boxWidth, 32, 6);
      ctx.fill();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1.2;
      ctx.stroke();

      ctx.font = 'bold 10px system-ui, -apple-system, sans-serif';
      ctx.fillStyle = isAtWar ? '#FCA5A5' : '#FDE68A';
      ctx.fillText(titleText, cx, badgeY + 10);

      ctx.font = '9px system-ui, -apple-system, sans-serif';
      ctx.fillStyle = '#CBD5E1';
      ctx.fillText(subtitleText, cx, badgeY + 23);

      ctx.restore();
    }

    ctx.restore();
  }

  private renderFertileOases(
    ctx: CanvasRenderingContext2D,
    clusters: [number, number][],
    clusterHomes?: Record<number, number>
  ) {
    if (!clusters || clusters.length === 0) return;
    ctx.save();

    clusters.forEach(([cx, cy], idx) => {
      const isHome = clusterHomes && clusterHomes[idx] !== undefined;
      const famId = isHome ? clusterHomes[idx] : null;

      if (isHome) {
        const clanName = getClanName(famId);

        // Halo suave do santuário do Clã
        const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 95);
        grad.addColorStop(0, 'rgba(16, 185, 129, 0.20)');
        grad.addColorStop(0.5, 'rgba(244, 63, 94, 0.08)');
        grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        ctx.beginPath();
        ctx.arc(cx, cy, 92, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        // Borda defensiva com anel de proteção
        ctx.beginPath();
        ctx.arc(cx, cy, 92, 0, Math.PI * 2);
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 1.8;
        ctx.setLineDash([8, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Anel interno de santuário do filhote
        ctx.beginPath();
        ctx.arc(cx, cy, 42, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(216, 180, 254, 0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Estandarte com Nome do Clã
        ctx.save();
        ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const badgeText = `🛡️ ${clanName} #${famId}`;
        const textWidth = ctx.measureText(badgeText).width;
        ctx.fillStyle = 'rgba(11, 17, 30, 0.90)';
        ctx.beginPath();
        ctx.roundRect(cx - textWidth / 2 - 8, cy - 105, textWidth + 16, 20, 10);
        ctx.fill();
        ctx.strokeStyle = 'rgba(52, 211, 153, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = '#6EE7B7';
        ctx.fillText(badgeText, cx, cy - 95);
        ctx.restore();
      } else {
        // Centro Fértil Neutro
        const grad = ctx.createRadialGradient(cx, cy, 5, cx, cy, 90);
        grad.addColorStop(0, 'rgba(56, 189, 248, 0.12)');
        grad.addColorStop(0.6, 'rgba(56, 189, 248, 0.02)');
        grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

        ctx.beginPath();
        ctx.arc(cx, cy, 90, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(cx, cy, 90, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.18)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 6]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    });

    ctx.restore();
  }

  private renderWorldBoundsAndGrid(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    showGrid: boolean
  ) {
    ctx.fillStyle = '#0B111E';
    ctx.fillRect(0, 0, w, h);

    if (showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const step = 60;
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

    ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    ctx.lineWidth = 2.0;
    ctx.strokeRect(0, 0, w, h);
  }

  private renderFoods(ctx: CanvasRenderingContext2D, foods: CompactFood[]) {
    ctx.save();
    for (const food of foods) {
      const [, fx, fy] = food;

      ctx.beginPath();
      ctx.arc(fx, fy, 3.8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(52, 211, 153, 0.25)';
      ctx.fill();

      ctx.beginPath();
      ctx.arc(fx, fy, 2.4, 0, Math.PI * 2);
      ctx.fillStyle = '#34D399';
      ctx.shadowColor = '#10B981';
      ctx.shadowBlur = 5;
      ctx.fill();
    }
    ctx.restore();
  }

  /**
   * Renderização simplificada, elegante e de altíssima legibilidade para cada habitante.
   */
  private renderOrganisms(
    ctx: CanvasRenderingContext2D,
    organisms: CompactOrganism[],
    options: RenderOptions,
    selectedId?: number | null,
    currentTick: number = 0
  ) {
    ctx.save();
    for (const org of organisms) {
      const heading = Math.atan2(org.vy, org.vx);
      const roleChar = org.r ?? 'M'; // 'F' (Rosa), 'M' (Verde), 'C' (Roxo)
      const isSelected = selectedId !== undefined && selectedId !== null && org.id === selectedId;

      // 1. Halo sensorial (se ativado)
      if (options.showSensoryRadius || isSelected) {
        ctx.beginPath();
        ctx.arc(org.x, org.y, 70, 0, Math.PI * 2);
        ctx.strokeStyle = isSelected ? 'rgba(56, 189, 248, 0.35)' : `hsla(${org.h}, 85%, 60%, 0.08)`;
        ctx.lineWidth = isSelected ? 1.5 : 0.8;
        ctx.stroke();
      }

      // 2. Retículo holográfico de seleção do animal escolhido
      if (isSelected) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(org.x, org.y, org.sz + 7, 0, Math.PI * 2);
        ctx.strokeStyle = '#38BDF8';
        ctx.lineWidth = 2.0;
        ctx.shadowColor = '#0EA5E9';
        ctx.shadowBlur = 8;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.restore();

        // Tag sobre a cabeça
        ctx.save();
        ctx.font = 'bold 10px system-ui, -apple-system, sans-serif';
        ctx.textAlign = 'center';
        let leaderPrefix = '';
        if (org.clr === 'A') leaderPrefix = '👑 [ALPHA] ';
        else if (org.clr === 'B') leaderPrefix = '⭐ [BETA] ';
        const tagText = `${leaderPrefix}${org.nm || `Animal #${org.id}`}`;
        const textWidth = ctx.measureText(tagText).width;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.beginPath();
        ctx.roundRect(org.x - textWidth / 2 - 5, org.y - org.sz - 20, textWidth + 10, 15, 4);
        ctx.fill();
        ctx.strokeStyle = org.clr === 'A' ? '#FBBF24' : org.clr === 'B' ? '#93C5FD' : '#38BDF8';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = org.clr === 'A' ? '#FEF08A' : org.clr === 'B' ? '#DBEAFE' : '#F8FAFC';
        ctx.fillText(tagText, org.x, org.y - org.sz - 9);
        ctx.restore();
      }

      ctx.save();
      ctx.translate(org.x, org.y);

      // Distintivo vertical para líderes Alpha e Beta
      if (org.clr === 'A') {
        // Alpha: Aura dourada pulsante e Coroa 👑
        ctx.beginPath();
        ctx.arc(0, 0, org.sz + 4, 0, Math.PI * 2);
        ctx.strokeStyle = '#FBBF24';
        ctx.lineWidth = 2.0;
        ctx.shadowColor = '#F59E0B';
        ctx.shadowBlur = 8;
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.font = '12px system-ui, -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('👑', 0, -org.sz - 4);
      } else if (org.clr === 'B') {
        // Beta: Aura celeste e Estrela ⭐
        ctx.beginPath();
        ctx.arc(0, 0, org.sz + 3.5, 0, Math.PI * 2);
        ctx.strokeStyle = '#93C5FD';
        ctx.lineWidth = 1.6;
        ctx.shadowColor = '#60A5FA';
        ctx.shadowBlur = 6;
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.font = '11px system-ui, -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('⭐', 0, -org.sz - 4);
      }

      ctx.rotate(heading);

      // Vetor de direção simplificado (traço sutil)
      if (options.showVelocityVectors) {
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(org.sz * 2.0, 0);
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.45)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Determinação de cor base vibrante e pura
      let mainColor = '#34D399'; // Verde
      let glowColor = '#10B981';
      if (roleChar === 'F') {
        mainColor = '#FB7185'; // Rosa
        glowColor = '#F43F5E';
      } else if (roleChar === 'C') {
        mainColor = '#C084FC'; // Roxo
        glowColor = '#A855F7';
      }

      // Corpo celular biológico simplificado (Círculo perfeito ou elipse suave)
      ctx.beginPath();
      ctx.ellipse(0, 0, org.sz * 1.15, org.sz * 0.95, 0, 0, Math.PI * 2);
      ctx.fillStyle = mainColor;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = isSelected ? 10 : 5;
      ctx.fill();

      // Borda sutil
      ctx.lineWidth = isSelected ? 1.8 : 1.0;
      ctx.strokeStyle = isSelected ? '#FFFFFF' : 'rgba(255, 255, 255, 0.7)';
      ctx.stroke();

      // Núcleo / Ponto sensorial de direção (olho bioluminescente)
      ctx.beginPath();
      ctx.arc(org.sz * 0.45, 0, org.sz * 0.28, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.shadowBlur = 0;
      ctx.fill();

      // Mini anel perimétrico de saúde (mostrado quando ferido)
      const maxHp = org.ms || 100;
      if (org.s < maxHp * 0.95) {
        const hpFraction = Math.max(0, Math.min(1.0, org.s / maxHp));
        ctx.beginPath();
        ctx.arc(0, 0, org.sz + 3, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * hpFraction);
        ctx.strokeStyle = hpFraction > 0.5 ? '#34D399' : hpFraction > 0.25 ? '#F59E0B' : '#EF4444';
        ctx.lineWidth = 1.6;
        ctx.stroke();
      }

      // Orbita satélite de alimento transportado para o ninho
      if (org.cf && org.cf > 0) {
        const orbitAngle = (currentTick * 0.15 + org.id) % (Math.PI * 2);
        const orbitRadius = org.sz + 5;
        const ox = Math.cos(orbitAngle) * orbitRadius;
        const oy = Math.sin(orbitAngle) * orbitRadius;

        ctx.beginPath();
        ctx.arc(ox, oy, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#FBBF24';
        ctx.shadowColor = '#F59E0B';
        ctx.shadowBlur = 6;
        ctx.fill();
      }

      // Indicador sutil de recém-nascido adormecido no ninho
      if (org.st === 'N') {
        ctx.beginPath();
        ctx.arc(0, 0, org.sz + 2, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(192, 132, 252, 0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      ctx.restore();
    }
    ctx.restore();
  }

  /** Renderiza fagulhas visuais de combate e cuidado parental */
  private renderSparks(ctx: CanvasRenderingContext2D) {
    if (this.sparks.length === 0) return;
    ctx.save();

    for (let i = this.sparks.length - 1; i >= 0; i--) {
      const spark = this.sparks[i];
      const progress = 1 - spark.life / spark.maxLife;
      const alpha = Math.max(0, spark.life / spark.maxLife);

      if (spark.type === 'combat') {
        // Efeito de corte/impacto
        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 8 + progress * 14, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(248, 113, 113, ${alpha * 0.8})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else if (spark.type === 'care') {
        // Efeito de carinho / alimentação parental
        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 6 + progress * 10, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(52, 211, 153, ${alpha * 0.7})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      } else {
        // Efeito de celebração / proclamação de clã
        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 10 + progress * 22, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(251, 191, 36, ${alpha * 0.8})`;
        ctx.lineWidth = 1.8;
        ctx.stroke();
      }

      // Texto flutuante que sobe suavemente
      if (spark.text) {
        ctx.font = 'bold 10px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = spark.color;
        ctx.globalAlpha = alpha;
        ctx.textAlign = 'center';
        ctx.fillText(spark.text, spark.x, spark.y - 12 - progress * 18);
        ctx.globalAlpha = 1.0;
      }

      spark.life -= 1;
      if (spark.life <= 0) {
        this.sparks.splice(i, 1);
      }
    }

    ctx.restore();
  }
}
