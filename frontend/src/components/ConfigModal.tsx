import React, { useState } from 'react';
import { X, Dna, Shuffle } from 'lucide-react';
import type { SimulationConfig } from '../types';

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: SimulationConfig;
  onApplyConfig: (newConfig: SimulationConfig) => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({
  isOpen,
  onClose,
  config,
  onApplyConfig,
}) => {
  const [seed, setSeed] = useState<number | null>(config.seed);
  const [initialOrganisms, setInitialOrganisms] = useState<number>(config.initial_organisms);
  const [initialFood, setInitialFood] = useState<number>(config.initial_food);
  const [foodSpawnRate, setFoodSpawnRate] = useState<number>(config.food_spawn_rate);
  const [maxFood, setMaxFood] = useState<number>(config.max_food);
  const [width, setWidth] = useState<number>(config.width);
  const [height, setHeight] = useState<number>(config.height);

  if (!isOpen) return null;

  const handleRandomizeSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onApplyConfig({
      seed,
      initial_organisms: initialOrganisms,
      initial_food: initialFood,
      food_spawn_rate: foodSpawnRate,
      max_food: maxFood,
      width,
      height,
    });
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '480px',
          padding: '24px',
          borderRadius: '16px',
          backgroundColor: '#0F1626',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Dna size={20} color="#38BDF8" />
            <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Parâmetros do Experimento</h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Seed PRNG */}
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
              Semente Determinística (PRNG Seed)
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="number"
                value={seed ?? ''}
                onChange={(e) => setSeed(e.target.value === '' ? null : Number(e.target.value))}
                placeholder="Ex: 42"
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: '8px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  color: '#F1F5F9',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                }}
              />
              <button
                type="button"
                onClick={handleRandomizeSeed}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: '#38BDF8',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <Shuffle size={14} /> Aleatória
              </button>
            </div>
            <span style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.4)', marginTop: '4px', display: 'block' }}>
              A mesma semente garante a reprodução estrita e idêntica dos resultados.
            </span>
          </div>

          {/* Grid de 2 colunas para população e comida */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                População Inicial: {initialOrganisms}
              </label>
              <input
                type="range"
                min="5"
                max="200"
                step="5"
                value={initialOrganisms}
                onChange={(e) => setInitialOrganisms(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--color-primary)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                Alimento Inicial: {initialFood}
              </label>
              <input
                type="range"
                min="10"
                max="400"
                step="10"
                value={initialFood}
                onChange={(e) => setInitialFood(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#10B981' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                Taxa Spawn Comida: {foodSpawnRate.toFixed(1)} / t
              </label>
              <input
                type="range"
                min="0.0"
                max="8.0"
                step="0.2"
                value={foodSpawnRate}
                onChange={(e) => setFoodSpawnRate(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#10B981' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                Capacidade Máx. Alimento: {maxFood}
              </label>
              <input
                type="range"
                min="50"
                max="600"
                step="25"
                value={maxFood}
                onChange={(e) => setMaxFood(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#10B981' }}
              />
            </div>
          </div>

          {/* Dimensões do Mundo */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                Largura do Mundo (px)
              </label>
              <input
                type="number"
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  color: '#F1F5F9',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
                Altura do Mundo (px)
              </label>
              <input
                type="number"
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  color: '#F1F5F9',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                }}
              />
            </div>
          </div>

          {/* Botões de Ação */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                border: '1px solid var(--border-subtle)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                background: '#0284C7',
                color: '#FFFFFF',
                border: 'none',
                fontSize: '13px',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 0 12px rgba(2, 132, 199, 0.4)',
              }}
            >
              Aplicar e Reiniciar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
