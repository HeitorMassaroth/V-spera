/**
 * Motor de renderização em HTML5 Canvas 2D de alta performance.
 * Visualização da simulação VÉSPERA: Organismos simplificados, combate dinâmico e oásis de clãs.
 */

import type { CompactOrganism, CompactFood, WorldEvent, NestInfo, ClanInfo, TerritoryZoneInfo, SeasonInfo } from '../types';
import { getClanName } from '../types';

export interface RenderOptions {
  showSensoryRadius: boolean;
  showVelocityVectors: boolean;
  showGridLines: boolean;
  showTerritories?: boolean;
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
  type: 'combat' | 'care' | 'clan' | 'birth' | 'bond';
}

interface TrailPoint {
  x: number;
  y: number;
}

interface WeatherParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  swayOffset: number;
}

export class WorldRenderer {
  private ctx: CanvasRenderingContext2D;
  public scale: number = 1.0;
  public offsetX: number = 0.0;
  public offsetY: number = 0.0;
  public dpr: number = 1.0;
  private sparks: VisualSpark[] = [];
  private lastProcessedTick: number = 0;
  private trails: Map<number, TrailPoint[]> = new Map();
  private weatherParticles: WeatherParticle[] = [];
  private weatherInitialized: boolean = false;

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
            text: '💕 Vínculo Eterno',
            color: '#FDA4AF',
            life: 40,
            maxLife: 40,
            type: 'bond',
          });
        } else if (ev.type === 'birth' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `✨ ${ev.child_name || 'Novo Habitante'} (G${ev.gen ?? 1})`,
            color: '#FDE047',
            life: 50,
            maxLife: 50,
            type: 'birth',
          });
        } else if (ev.type === 'nest_created' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `🪺 Novo Ninho Estabelecido`,
            color: '#34D399',
            life: 45,
            maxLife: 45,
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
        } else if (ev.type === 'vranco_collective_defense' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: `🛡️ Mobbing Vranco! (-${ev.damage?.toFixed(1) || 'repel'})`,
            color: '#F59E0B',
            life: 40,
            maxLife: 40,
            type: 'combat',
          });
        } else if (ev.type === 'predator_defeated' && ev.x !== undefined && ev.y !== undefined) {
          this.sparks.push({
            x: ev.x,
            y: ev.y,
            text: '⚔️ Predador Vencido!',
            color: '#34D399',
            life: 45,
            maxLife: 45,
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
    clans?: ClanInfo[],
    territories?: TerritoryZoneInfo[],
    season?: SeasonInfo | null
  ) {
    const ctx = this.ctx;
    ctx.save();

    // Aplica escala de alta resolução física (Retina / 4K / High-DPI - BUG-04)
    if (this.dpr && this.dpr !== 1.0) {
      ctx.scale(this.dpr, this.dpr);
    }

    this.ingestEvents(events, currentTick);

    // Limpa fundo
    ctx.fillStyle = '#080C14';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Aplica transformações de câmera (Pan & Zoom)
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);

    // 1. Limites do ecossistema e grade espacial com iluminação ambiental da estação
    this.renderWorldBoundsAndGrid(ctx, options.worldWidth, options.worldHeight, options.showGridLines, season, currentTick);

    // 1.5 Territórios Regionais e Indicadores de Qualidade Ecológica
    if (options.showTerritories !== false) {
      this.renderTerritoryZones(ctx, territories, currentTick);
    }

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

  /**
   * Renderiza as 8 Regiões Territoriais, Qualidade Ecológica, Áreas Disputadas e Santuários Periféricos
   */
  private renderTerritoryZones(
    ctx: CanvasRenderingContext2D,
    territories?: TerritoryZoneInfo[],
    currentTick: number = 0
  ) {
    if (!territories || territories.length === 0) return;
    ctx.save();

    for (const zone of territories) {
      const { x, y, radius, quality_score, status, name, food_count, occupants_count, carrying_capacity, safety_score, is_peripheral } = zone;

      // Determinação estética por status político e qualidade ambiental
      let strokeColor = 'rgba(56, 189, 248, 0.45)';
      let fillColor = 'rgba(56, 189, 248, 0.05)';
      let statusTag = '🗺️ LIVRE';
      let tagBg = 'rgba(15, 23, 42, 0.88)';
      let pulse = 0;

      if (status === 'CONTESTED') {
        pulse = Math.sin(currentTick * 0.18) * 5;
        strokeColor = 'rgba(239, 68, 68, 0.88)';
        fillColor = 'rgba(239, 68, 68, 0.14)';
        statusTag = '⚔️ DISPUTA ATIVA';
        tagBg = 'rgba(69, 10, 10, 0.92)';
      } else if (status === 'DEGRADED') {
        strokeColor = 'rgba(148, 163, 184, 0.40)';
        fillColor = 'rgba(100, 116, 139, 0.06)';
        statusTag = '⚠️ DEGRADADO';
        tagBg = 'rgba(30, 41, 59, 0.88)';
      } else if (status === 'ABANDONED') {
        strokeColor = 'rgba(217, 119, 6, 0.50)';
        fillColor = 'rgba(217, 119, 6, 0.06)';
        statusTag = '⏳ POUSIO';
        tagBg = 'rgba(45, 26, 8, 0.88)';
      } else if (status === 'SETTLED') {
        strokeColor = 'rgba(16, 185, 129, 0.65)';
        fillColor = 'rgba(16, 185, 129, 0.08)';
        statusTag = is_peripheral ? '🛡️ SANTUÁRIO' : '🏰 HABITADO';
        tagBg = 'rgba(6, 44, 30, 0.90)';
      } else {
        // UNCLAIMED
        if (is_peripheral) {
          strokeColor = 'rgba(139, 92, 246, 0.45)';
          fillColor = 'rgba(139, 92, 246, 0.05)';
          statusTag = '🌿 REFÚGIO';
        }
      }

      const effectiveRadius = radius + pulse;

      // 1. Halo expansivo de qualidade ecológica
      const grad = ctx.createRadialGradient(x, y, 10, x, y, effectiveRadius);
      grad.addColorStop(0, fillColor);
      grad.addColorStop(0.75, fillColor);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.arc(x, y, effectiveRadius, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // 2. Fronteira pontilhada territorial
      ctx.beginPath();
      ctx.arc(x, y, effectiveRadius, 0, Math.PI * 2);
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = status === 'CONTESTED' ? 2.2 : 1.4;
      ctx.setLineDash(status === 'CONTESTED' ? [4, 4] : [8, 6]);
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Estandarte com nome e indicadores de qualidade
      ctx.save();
      ctx.font = 'bold 9px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const title = `${name} [${statusTag}]`;
      const subtitle = `⭐ ${quality_score.toFixed(0)}% • 🥩 ${food_count} • 👥 ${occupants_count}/${carrying_capacity} • 🛡️ ${(safety_score * 100).toFixed(0)}%`;

      const titleWidth = ctx.measureText(title).width;
      ctx.font = '8px system-ui, -apple-system, sans-serif';
      const subWidth = ctx.measureText(subtitle).width;
      const boxWidth = Math.max(titleWidth, subWidth) + 18;
      const boxHeight = 26;
      const badgeY = y - effectiveRadius - 16;

      ctx.fillStyle = tagBg;
      ctx.beginPath();
      ctx.roundRect(x - boxWidth / 2, badgeY, boxWidth, boxHeight, 5);
      ctx.fill();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.font = 'bold 9px system-ui, -apple-system, sans-serif';
      ctx.fillStyle = status === 'CONTESTED' ? '#FCA5A5' : status === 'DEGRADED' ? '#CBD5E1' : '#FDE68A';
      ctx.fillText(title, x, badgeY + 8);

      ctx.font = '8px system-ui, -apple-system, sans-serif';
      ctx.fillStyle = '#94A3B8';
      ctx.fillText(subtitle, x, badgeY + 19);

      ctx.restore();
    }

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
      ctx.lineWidth = nest.level === 3 ? 2.4 : 1.8;
      ctx.setLineDash([5, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Núcleo central do ninho
      ctx.beginPath();
      ctx.arc(nest.x, nest.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(251, 191, 36, 0.4)';
      ctx.fill();

      // Pontos de comida armazenada no ninho
      if (nest.food_storage > 0) {
        const dots = Math.min(6, Math.max(1, Math.ceil(nest.food_storage / 15)));
        for (let d = 0; d < dots; d++) {
          const angle = (d / dots) * Math.PI * 2;
          const fx = nest.x + Math.cos(angle) * 11;
          const fy = nest.y + Math.sin(angle) * 11;
          ctx.beginPath();
          ctx.arc(fx, fy, 2.2, 0, Math.PI * 2);
          ctx.fillStyle = '#34D399';
          ctx.shadowColor = '#10B981';
          ctx.shadowBlur = 4;
          ctx.fill();
        }
        ctx.shadowBlur = 0;
      }

      // Tag sobre o ninho com clã, nível e estoque
      ctx.save();
      ctx.font = 'bold 9px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';
      const clanName = getClanName(nest.family_id);
      const lvlBadge = nest.level > 1 ? `[Nv.${nest.level}] ` : '';
      const tagText = `🪹 ${lvlBadge}${clanName} • 🌿${nest.food_storage.toFixed(0)}`;
      const textWidth = ctx.measureText(tagText).width;

      ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
      ctx.beginPath();
      ctx.roundRect(nest.x - textWidth / 2 - 5, nest.y - 34, textWidth + 10, 14, 4);
      ctx.fill();
      ctx.strokeStyle = nest.level === 3 ? '#F59E0B' : 'rgba(251, 191, 36, 0.4)';
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.fillStyle = nest.level === 3 ? '#FEF08A' : '#FDE68A';
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

  private initWeather(worldWidth: number, worldHeight: number) {
    if (this.weatherInitialized && this.weatherParticles.length > 0) return;
    this.weatherParticles = [];
    const count = 45;
    for (let i = 0; i < count; i++) {
      this.weatherParticles.push({
        x: Math.random() * worldWidth,
        y: Math.random() * worldHeight,
        vx: (Math.random() - 0.5) * 0.4,
        vy: 0.2 + Math.random() * 0.5,
        size: 1.2 + Math.random() * 1.8,
        alpha: 0.2 + Math.random() * 0.4,
        swayOffset: Math.random() * Math.PI * 2,
      });
    }
    this.weatherInitialized = true;
  }

  private renderWeather(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    season?: SeasonInfo | null,
    currentTick: number = 0
  ) {
    if (!season) return;
    this.initWeather(w, h);

    const sType = season.season;
    let particleColor = 'rgba(255, 255, 255,';
    let speedMult = 1.0;

    if (sType === 'SPRING') {
      particleColor = 'rgba(167, 243, 208,';
      speedMult = 0.6;
    } else if (sType === 'SUMMER') {
      particleColor = 'rgba(253, 230, 138,';
      speedMult = 0.8;
    } else if (sType === 'AUTUMN') {
      particleColor = 'rgba(251, 146, 60,';
      speedMult = 1.2;
    } else if (sType === 'WINTER') {
      particleColor = 'rgba(186, 230, 253,';
      speedMult = 1.0;
    }

    ctx.save();
    for (const p of this.weatherParticles) {
      const sway = Math.sin(currentTick * 0.04 + p.swayOffset) * 0.5;
      p.x += (p.vx + sway) * speedMult;
      p.y += p.vy * speedMult;

      if (p.x < 0) p.x = w;
      if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h;
      if (p.y > h) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `${particleColor} ${p.alpha})`;
      ctx.fill();
    }
    ctx.restore();
  }

  private renderWorldBoundsAndGrid(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    showGrid: boolean,
    season?: SeasonInfo | null,
    currentTick: number = 0
  ) {
    ctx.fillStyle = '#0B111E';
    ctx.fillRect(0, 0, w, h);

    // Iluminação ambiental suave e imersiva de acordo com a estação climática
    if (season) {
      if (season.season === 'SPRING') {
        ctx.fillStyle = 'rgba(16, 185, 129, 0.035)';
        ctx.fillRect(0, 0, w, h);
      } else if (season.season === 'SUMMER') {
        ctx.fillStyle = 'rgba(245, 158, 11, 0.04)';
        ctx.fillRect(0, 0, w, h);
      } else if (season.season === 'AUTUMN') {
        ctx.fillStyle = 'rgba(234, 88, 12, 0.035)';
        ctx.fillRect(0, 0, w, h);
      } else if (season.season === 'WINTER') {
        ctx.fillStyle = 'rgba(56, 189, 248, 0.045)';
        ctx.fillRect(0, 0, w, h);
      }
    }

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

    const strokeColor = season
      ? season.season === 'SPRING'
        ? 'rgba(16, 185, 129, 0.35)'
        : season.season === 'SUMMER'
        ? 'rgba(245, 158, 11, 0.35)'
        : season.season === 'AUTUMN'
        ? 'rgba(234, 88, 12, 0.35)'
        : 'rgba(56, 189, 248, 0.35)'
      : 'rgba(56, 189, 248, 0.3)';

    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2.0;
    ctx.strokeRect(0, 0, w, h);

    // Renderiza partículas climáticas sazonais
    this.renderWeather(ctx, w, h, season, currentTick);
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

    // 0.1 Limpeza de rastros de organismos falecidos
    const activeIds = new Set(organisms.map(o => o.id));
    for (const id of this.trails.keys()) {
      if (!activeIds.has(id)) {
        this.trails.delete(id);
      }
    }

    // 0.2 Atualização dos rastros de nado/movimento
    for (const org of organisms) {
      let t = this.trails.get(org.id);
      if (!t) {
        t = [];
        this.trails.set(org.id, t);
      }
      t.push({ x: org.x, y: org.y });
      if (t.length > 5) {
        t.shift();
      }
    }

    // 0.3 Desenho das caudas bioluminescentes (rastros de movimento)
    for (const org of organisms) {
      const t = this.trails.get(org.id);
      if (t && t.length > 1) {
        ctx.beginPath();
        ctx.moveTo(t[0].x, t[0].y);
        for (let i = 1; i < t.length; i++) {
          ctx.lineTo(t[i].x, t[i].y);
        }
        const isVranco = org.sp === 'V';
        const trailColor = isVranco
          ? 'rgba(245, 158, 11,'
          : org.r === 'F'
          ? 'rgba(251, 113, 133,'
          : 'rgba(52, 211, 153,';
        ctx.strokeStyle = `${trailColor} 0.18)`;
        ctx.lineWidth = Math.max(1, org.sz * 0.45);
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();
      }
    }

    // 0.4 Vínculos românticos / tethers entre casais monogâmicos próximos
    const familyMates = new Map<number, { m?: CompactOrganism; f?: CompactOrganism }>();
    for (const org of organisms) {
      if (org.fam !== undefined && org.fam !== null && org.r !== 'C') {
        let entry = familyMates.get(org.fam);
        if (!entry) {
          entry = {};
          familyMates.set(org.fam, entry);
        }
        if (org.r === 'M') entry.m = org;
        else if (org.r === 'F') entry.f = org;
      }
    }

    for (const [, pair] of familyMates) {
      if (pair.m && pair.f) {
        const dx = pair.m.x - pair.f.x;
        const dy = pair.m.y - pair.f.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < 140 && d > 12) {
          const tetherAlpha = Math.max(0, (1 - d / 140) * 0.32);
          ctx.beginPath();
          ctx.moveTo(pair.m.x, pair.m.y);
          ctx.lineTo(pair.f.x, pair.f.y);
          ctx.strokeStyle = `rgba(251, 113, 133, ${tetherAlpha})`;
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    }

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
        const isVranco = org.sp === 'V';
        const speciesPrefix = isVranco ? '⚡ [VRANCO] ' : '🐺 [PREDADOR] ';
        const tagText = `${speciesPrefix}${leaderPrefix}${org.nm || `Animal #${org.id}`}`;
        const textWidth = ctx.measureText(tagText).width;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.beginPath();
        ctx.roundRect(org.x - textWidth / 2 - 5, org.y - org.sz - 20, textWidth + 10, 15, 4);
        ctx.fill();
        ctx.strokeStyle = isVranco ? '#F59E0B' : (org.clr === 'A' ? '#FBBF24' : org.clr === 'B' ? '#93C5FD' : '#38BDF8');
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = isVranco ? '#FEF08A' : (org.clr === 'A' ? '#FEF08A' : org.clr === 'B' ? '#DBEAFE' : '#F8FAFC');
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
      const isVranco = org.sp === 'V';
      let mainColor = '#34D399'; // Predador Macho (Verde Esmeralda)
      let glowColor = '#10B981';

      if (isVranco) {
        // Raça Vrancos: Tons dourados, âmbar e areia quentes e velozes
        if (roleChar === 'F') {
          mainColor = '#FB923C'; // Âmbar Coral
          glowColor = '#EA580C';
        } else if (roleChar === 'C') {
          mainColor = '#FDE047'; // Ouro Pálido/Areia
          glowColor = '#EAB308';
        } else {
          mainColor = '#F59E0B'; // Ouro Imperial
          glowColor = '#D97706';
        }
      } else {
        // Predadores Tradicionais
        if (roleChar === 'F') {
          mainColor = '#FB7185'; // Rosa Rubro
          glowColor = '#F43F5E';
        } else if (roleChar === 'C') {
          mainColor = '#C084FC'; // Roxo
          glowColor = '#A855F7';
        }
      }

      // Calda / Crista aerodinâmica distintiva para Vrancos (maior agilidade visual)
      if (isVranco) {
        ctx.beginPath();
        ctx.moveTo(-org.sz * 0.5, 0);
        ctx.lineTo(-org.sz * 1.5, -org.sz * 0.4);
        ctx.lineTo(-org.sz * 1.1, 0);
        ctx.lineTo(-org.sz * 1.5, org.sz * 0.4);
        ctx.closePath();
        ctx.fillStyle = glowColor;
        ctx.fill();
      }

      // Corpo celular biológico simplificado
      ctx.beginPath();
      if (isVranco) {
        ctx.ellipse(0, 0, org.sz * 1.30, org.sz * 0.85, 0, 0, Math.PI * 2);
      } else {
        ctx.ellipse(0, 0, org.sz * 1.15, org.sz * 0.95, 0, 0, Math.PI * 2);
      }
      ctx.fillStyle = mainColor;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = isSelected ? 12 : (isVranco ? 7 : 5);
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
      } else if (spark.type === 'birth') {
        // Efeito de nascimento (halo dourado radiante)
        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 6 + progress * 24, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(253, 224, 71, ${alpha * 0.85})`;
        ctx.lineWidth = 2.0;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 3 + progress * 12, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(254, 240, 138, ${alpha * 0.35})`;
        ctx.fill();
      } else if (spark.type === 'bond') {
        // Efeito de vínculo de acasalamento (aura rosa radiante)
        ctx.beginPath();
        ctx.arc(spark.x, spark.y, 8 + progress * 18, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(253, 164, 175, ${alpha * 0.85})`;
        ctx.lineWidth = 1.8;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
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
