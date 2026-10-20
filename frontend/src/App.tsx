import React, { useState, useCallback } from 'react';
import { useSimulationSocket } from './hooks/useSimulationSocket';
import { TopBar } from './components/TopBar';
import { SimulationViewer } from './components/SimulationViewer';
import { MetricsPanel } from './components/MetricsPanel';
import { ConfigModal } from './components/ConfigModal';
import type { SimulationConfig } from './types';

export const App: React.FC = () => {
  const {
    connected,
    isReconnecting,
    reconnect,
    status,
    tps,
    organisms,
    foods,
    clusters,
    clusterHomes,
    families,
    nests,
    clans,
    territories,
    season,
    ecology,
    metrics,
    events,
    metricsHistory,
    play,
    pause,
    step,
    reset,
    setSpeed,
    spawnFood,
  } = useSimulationSocket();

  const [selectedOrganismId, setSelectedOrganismId] = useState<number | null>(null);

  const [config, setConfig] = useState<SimulationConfig>({
    seed: 42,
    width: 1200,
    height: 800,
    initial_organisms: null,
    initial_food: 120,
    food_spawn_rate: 1.8,
    max_food: 250,
  });

  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);

  const handlePlayPauseToggle = useCallback(() => {
    if (status === 'RUNNING') {
      pause();
    } else {
      play();
    }
  }, [status, pause, play]);

  const handleApplyConfig = useCallback(
    async (newConfig: SimulationConfig) => {
      setConfig(newConfig);
      try {
        await fetch('http://localhost:8000/api/simulation/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            seed: newConfig.seed,
            width: newConfig.width,
            height: newConfig.height,
            initial_organisms: newConfig.initial_organisms,
            initial_predator_females: newConfig.initial_predator_females,
            initial_predator_males: newConfig.initial_predator_males,
            initial_vranco_females: newConfig.initial_vranco_females,
            initial_vranco_males: newConfig.initial_vranco_males,
            initial_food: newConfig.initial_food,
            food_spawn_rate: newConfig.food_spawn_rate,
            max_food: newConfig.max_food,
          }),
        });
      } catch (err) {
        console.error('Erro ao aplicar nova configuração:', err);
      }
    },
    []
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Barra de Controle Superior */}
      <TopBar
        connected={connected}
        status={status}
        tps={tps}
        tick={metrics?.tick ?? 0}
        isExtinct={metrics?.is_extinct ?? false}
        season={season ?? metrics?.season}
        isReconnecting={isReconnecting}
        onReconnect={reconnect}
        onPlay={play}
        onPause={pause}
        onStep={step}
        onReset={() => reset(config.seed ?? undefined)}
        onSpeedChange={setSpeed}
        onOpenConfig={() => setIsConfigOpen(true)}
      />

      {/* Área Central: Visualizador Canvas 2D + Painel de Telemetria Lateral */}
      <main style={{ display: 'flex', flex: 1, minHeight: 0, position: 'relative' }}>
        <div style={{ flex: 1, position: 'relative', height: '100%', overflow: 'hidden' }}>
          <SimulationViewer
            organisms={organisms}
            foods={foods}
            clusters={clusters}
            clusterHomes={clusterHomes}
            nests={nests}
            clans={clans}
            territories={territories}
            season={season ?? metrics?.season}
            populationAverages={metrics?.attr_stats}
            events={events}
            tick={metrics?.tick ?? 0}
            worldWidth={config.width}
            worldHeight={config.height}
            selectedOrganismId={selectedOrganismId}
            onSelectOrganism={setSelectedOrganismId}
            onSpawnFood={spawnFood}
            onPlayPauseToggle={handlePlayPauseToggle}
            onStep={step}
            onReset={() => reset(config.seed ?? undefined)}
            onSpeedChange={setSpeed}
            tps={tps}
          />
        </div>

        <MetricsPanel
          metrics={metrics}
          season={season ?? metrics?.season}
          ecology={ecology ?? metrics?.ecology}
          events={events}
          organisms={organisms}
          families={families}
          nests={nests}
          clans={clans}
          territories={territories}
          history={metricsHistory}
          onSelectOrganism={setSelectedOrganismId}
        />
      </main>

      {/* Modal de Configuração de Parâmetros */}
      <ConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        config={config}
        onApplyConfig={handleApplyConfig}
      />
    </div>
  );
};

export default App;
