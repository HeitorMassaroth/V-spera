import React, { useState } from 'react';
import { Play, Pause, SkipForward, RotateCcw, SlidersHorizontal, Activity, Wifi, WifiOff, Volume2, VolumeX } from 'lucide-react';
import type { SeasonInfo } from '../types';
import { soundManager } from '../audio/SoundManager';

interface TopBarProps {
  connected: boolean;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  tps: number;
  tick: number;
  isExtinct: boolean;
  season?: SeasonInfo | null;
  isReconnecting?: boolean;
  onReconnect?: () => void;
  onPlay: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
  onSpeedChange: (tps: number) => void;
  onOpenConfig: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  connected,
  status,
  tps,
  tick,
  isExtinct,
  season,
  isReconnecting,
  onReconnect,
  onPlay,
  onPause,
  onStep,
  onReset,
  onSpeedChange,
  onOpenConfig,
}) => {
  const [muted, setMuted] = useState<boolean>(soundManager.isMuted());

  const handleToggleAudio = () => {
    const next = soundManager.toggleMute();
    setMuted(next);
  };

  return (
    <header
      style={{
        height: '64px',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(10, 15, 26, 0.95)',
        backdropFilter: 'blur(10px)',
        zIndex: 50,
      }}
    >
      {/* Brand & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284C7, #10B981)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(56, 189, 248, 0.35)',
            }}
          >
            <Activity size={18} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '0.08em', color: '#F8FAFC' }}>
                VÉSPERA
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'rgba(56, 189, 248, 0.12)',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                v0.1 · Fase 1
              </span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', letterSpacing: '0.02em' }}>
              Laboratório de Vida Artificial & Ecossistemas Emergentes
            </p>
          </div>
        </div>

        {/* Status Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '999px',
            fontSize: '11px',
            fontWeight: 600,
            background: isExtinct
              ? 'rgba(239, 68, 68, 0.15)'
              : status === 'RUNNING'
              ? 'rgba(16, 185, 129, 0.15)'
              : 'rgba(245, 158, 11, 0.15)',
            color: isExtinct ? '#EF4444' : status === 'RUNNING' ? '#10B981' : '#F59E0B',
            border: `1px solid ${
              isExtinct ? 'rgba(239, 68, 68, 0.3)' : status === 'RUNNING' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'
            }`,
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isExtinct ? '#EF4444' : status === 'RUNNING' ? '#10B981' : '#F59E0B',
              boxShadow: `0 0 6px ${isExtinct ? '#EF4444' : status === 'RUNNING' ? '#10B981' : '#F59E0B'}`,
            }}
          />
          {isExtinct ? 'POPULAÇÃO EXTINTA' : status === 'RUNNING' ? 'SIMULANDO' : 'PAUSADO'}
        </div>

        {/* Season & Climate Indicator */}
        {season && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 12px',
              borderRadius: '999px',
              fontSize: '11px',
              fontWeight: 600,
              background:
                season.season === 'SPRING'
                  ? 'rgba(16, 185, 129, 0.12)'
                  : season.season === 'SUMMER'
                  ? 'rgba(245, 158, 11, 0.12)'
                  : season.season === 'AUTUMN'
                  ? 'rgba(234, 88, 12, 0.12)'
                  : 'rgba(56, 189, 248, 0.12)',
              border: `1px solid ${
                season.season === 'SPRING'
                  ? 'rgba(16, 185, 129, 0.35)'
                  : season.season === 'SUMMER'
                  ? 'rgba(245, 158, 11, 0.35)'
                  : season.season === 'AUTUMN'
                  ? 'rgba(234, 88, 12, 0.35)'
                  : 'rgba(56, 189, 248, 0.35)'
              }`,
              color:
                season.season === 'SPRING'
                  ? '#34D399'
                  : season.season === 'SUMMER'
                  ? '#FBBF24'
                  : season.season === 'AUTUMN'
                  ? '#FB923C'
                  : '#38BDF8',
            }}
            title={`${season.season_name} (Ano ${season.year}): ${season.season_desc} | Temp: ${season.temperature.toFixed(1)}°C | Spawn: ${season.food_spawn_multiplier.toFixed(2)}x | Gasto: ${season.metabolic_cost_multiplier.toFixed(2)}x`}
          >
            <span style={{ fontSize: '13px' }}>{season.season_icon}</span>
            <span style={{ fontWeight: 700, letterSpacing: '0.02em' }}>
              {season.season_name} · Ano {season.year}
            </span>
            <span
              style={{
                fontSize: '10px',
                padding: '1px 5px',
                borderRadius: '4px',
                background: 'rgba(255, 255, 255, 0.1)',
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              {season.temperature.toFixed(1)}°C
            </span>
            <div
              style={{
                width: '38px',
                height: '4px',
                borderRadius: '2px',
                background: 'rgba(255, 255, 255, 0.15)',
                overflow: 'hidden',
              }}
              title={`Progresso da Estação: ${Math.round(season.season_progress * 100)}%`}
            >
              <div
                style={{
                  width: `${Math.round(season.season_progress * 100)}%`,
                  height: '100%',
                  background: 'currentColor',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Play/Pause */}
        {status === 'RUNNING' ? (
          <button
            onClick={onPause}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              background: '#EAB308',
              color: '#0F172A',
              fontWeight: 700,
              fontSize: '13px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            title="Pausar simulação (Espaço)"
          >
            <Pause size={15} /> Pausar
          </button>
        ) : (
          <button
            onClick={onPlay}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              background: '#10B981',
              color: '#0F172A',
              fontWeight: 700,
              fontSize: '13px',
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 0 14px rgba(16, 185, 129, 0.4)',
              transition: 'all 0.15s ease',
            }}
            title="Iniciar simulação (Espaço)"
          >
            <Play size={15} /> Iniciar
          </button>
        )}

        {/* Step */}
        <button
          onClick={onStep}
          disabled={status === 'RUNNING'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            borderRadius: '8px',
            background: 'var(--bg-surface-elevated)',
            color: status === 'RUNNING' ? 'rgba(255, 255, 255, 0.3)' : '#F1F5F9',
            fontWeight: 600,
            fontSize: '13px',
            border: '1px solid var(--border-subtle)',
            cursor: status === 'RUNNING' ? 'not-allowed' : 'pointer',
          }}
          title="Avançar 1 ciclo (Step)"
        >
          <SkipForward size={14} /> Passo
        </button>

        {/* Reset */}
        <button
          onClick={onReset}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            borderRadius: '8px',
            background: 'var(--bg-surface-elevated)',
            color: '#F1F5F9',
            fontWeight: 600,
            fontSize: '13px',
            border: '1px solid var(--border-subtle)',
            cursor: 'pointer',
          }}
          title="Reiniciar com semente atual"
        >
          <RotateCcw size={14} /> Reiniciar
        </button>

        {/* Speed Slider */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 12px',
            borderRadius: '8px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>TPS:</span>
          <input
            type="range"
            min="5"
            max="60"
            step="5"
            value={tps}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            style={{ width: '80px', accentColor: 'var(--color-primary)', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '12px', fontWeight: 700, minWidth: '32px', textAlign: 'right', color: '#38BDF8' }}>
            {tps}
          </span>
        </div>

        {/* Config Modal Button */}
        <button
          onClick={onOpenConfig}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '8px',
            background: 'var(--bg-surface-elevated)',
            color: '#38BDF8',
            fontWeight: 600,
            fontSize: '13px',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            cursor: 'pointer',
          }}
          title="Configurar Parâmetros do Experimento"
        >
          <SlidersHorizontal size={15} /> Parâmetros
        </button>

        {/* Audio Procedural Toggle Button */}
        <button
          onClick={handleToggleAudio}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '8px',
            background: muted ? 'rgba(255, 255, 255, 0.04)' : 'rgba(16, 185, 129, 0.15)',
            color: muted ? '#94A3B8' : '#34D399',
            fontWeight: 600,
            fontSize: '13px',
            border: `1px solid ${muted ? 'rgba(255, 255, 255, 0.1)' : 'rgba(16, 185, 129, 0.35)'}`,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          title={muted ? 'Áudio Procedural Desativado (Clique para ativar sonorização nativa)' : 'Áudio Procedural Ativo (Web Audio API)'}
        >
          {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          <span>{muted ? 'Mudo' : 'Som'}</span>
        </button>
      </div>

      {/* Connection & Telemetry info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Ciclo Atual
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: '#F1F5F9' }}>
            t = {tick.toLocaleString()}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: connected ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${connected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.35)'}`,
            color: connected ? '#10B981' : '#FCA5A5',
          }}
          title={connected ? 'Conectado ao servidor' : 'Conexão interrompida. Tentando reconectar...'}
        >
          {connected ? <Wifi size={15} /> : <WifiOff size={15} />}
          <span>{connected ? 'Ao vivo' : isReconnecting ? 'Reconectando...' : 'Offline'}</span>
          {!connected && onReconnect && (
            <button
              onClick={onReconnect}
              style={{
                marginLeft: '2px',
                padding: '2px 6px',
                fontSize: '10px',
                fontWeight: 700,
                borderRadius: '4px',
                background: 'rgba(239, 68, 68, 0.25)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                color: '#FFFFFF',
                cursor: 'pointer',
              }}
              title="Forçar tentativa de reconexão imediata"
            >
              Reconectar
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
