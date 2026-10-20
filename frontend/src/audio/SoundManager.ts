/**
 * Gerenciador de Áudio Procedural Nativo (Web Audio API) para o VÉSPERA.
 * Sintetiza sonorização biológica em tempo real sem carregar arquivos de áudio externos.
 */

class SoundManager {
  private ctx: AudioContext | null = null;
  private muted: boolean = false;
  private initialized: boolean = false;
  private lastPlayed: Record<string, number> = {};

  constructor() {
    try {
      const saved = localStorage.getItem('vespera_muted');
      this.muted = saved !== null ? saved === 'true' : true; // Por padrão, mudo até o usuário ligar
    } catch {
      this.muted = true;
    }
  }

  private initContext() {
    if (this.ctx || typeof window === 'undefined') return;
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
        this.initialized = true;
      }
    } catch (e) {
      console.warn('Web Audio API não suportada neste ambiente:', e);
    }
  }

  public isInitialized(): boolean {
    return this.initialized;
  }

  public isMuted(): boolean {
    return this.muted;
  }

  public setMuted(muted: boolean) {
    this.muted = muted;
    try {
      localStorage.setItem('vespera_muted', String(muted));
    } catch {}
  }

  public toggleMute(): boolean {
    this.setMuted(!this.muted);
    if (!this.muted) {
      this.initContext();
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }
    return this.muted;
  }

  private shouldThrottle(key: string, cooldownMs = 120): boolean {
    const now = Date.now();
    const last = this.lastPlayed[key] || 0;
    if (now - last < cooldownMs) return true;
    this.lastPlayed[key] = now;
    return false;
  }

  /**
   * Efeito sonoro suave de nascimento: arpeggio harmônico ascendente
   */
  public playBirth() {
    if (this.muted || this.shouldThrottle('birth', 150)) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const notes = [523.25, 659.25, 783.99]; // Dó, Mi, Sol (C5, E5, G5)
      notes.forEach((freq, idx) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);

        gain.gain.setValueAtTime(0.001, now + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.12, now + idx * 0.08 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.08 + 0.28);

        osc.connect(gain);
        gain.connect(this.ctx!.destination);

        osc.start(now + idx * 0.08);
        osc.stop(now + idx * 0.08 + 0.3);
      });
    } catch {}
  }

  /**
   * Efeito sonoro de combate / predação: impacto percussivo abafado
   */
  public playCombat() {
    if (this.muted || this.shouldThrottle('combat', 100)) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(120, now);
      osc.frequency.exponentialRampToValueAtTime(38, now + 0.16);

      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.2);
    } catch {}
  }

  /**
   * Efeito sonoro de vínculo monogâmico (acasalamento): acorde doce suave
   */
  public playBond() {
    if (this.muted || this.shouldThrottle('bond', 200)) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now); // Lá (A4)
      osc.frequency.exponentialRampToValueAtTime(587.33, now + 0.25); // Ré (D5)

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.10, now + 0.08);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.5);
    } catch {}
  }

  /**
   * Efeito sonoro de proclamação de clã / líder Alpha: acorde tríade ressonante
   */
  public playClan() {
    if (this.muted || this.shouldThrottle('clan', 300)) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const freqs = [220, 277.18, 329.63, 440]; // A3 Major
      freqs.forEach((f) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(f, now);

        gain.gain.setValueAtTime(0.001, now);
        gain.gain.linearRampToValueAtTime(0.08, now + 0.06);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);

        osc.connect(gain);
        gain.connect(this.ctx!.destination);

        osc.start(now);
        osc.stop(now + 0.65);
      });
    } catch {}
  }

  /**
   * Efeito sonoro de mudança de estação climática: sino eólico etéreo
   */
  public playSeasonChange() {
    if (this.muted || this.shouldThrottle('season', 1000)) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(659.25, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.6);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.09, now + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.9);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.95);
    } catch {}
  }
}

export const soundManager = new SoundManager();
