import { useEffect, useRef, useState, useCallback } from 'react';
import type { CompactOrganism, CompactFood, WorldMetrics, SimulationStateMessage } from '../types';

export function useSimulationSocket(wsUrl: string = 'ws://localhost:8000/api/simulation/ws') {
  const [connected, setConnected] = useState<boolean>(false);
  const [status, setStatus] = useState<'RUNNING' | 'PAUSED' | 'STOPPED'>('PAUSED');
  const [tps, setTps] = useState<number>(30);
  const [organisms, setOrganisms] = useState<CompactOrganism[]>([]);
  const [foods, setFoods] = useState<CompactFood[]>([]);
  const [clusters, setClusters] = useState<[number, number][]>([]);
  const [metrics, setMetrics] = useState<WorldMetrics | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<
    Array<{ tick: number; pop: number; food: number; avgEnergy: number }>
  >([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const data: SimulationStateMessage = JSON.parse(event.data);
          if (data.status) setStatus(data.status);
          if (data.tps) setTps(data.tps);
          if (data.orgs) setOrganisms(data.orgs);
          if (data.foods) setFoods(data.foods);
          if (data.clusters) setClusters(data.clusters);
          if (data.metrics) {
            setMetrics(data.metrics);
            setMetricsHistory((prev) => {
              const updated = [
                ...prev,
                {
                  tick: data.metrics.tick,
                  pop: data.metrics.population,
                  food: data.metrics.food_count,
                  avgEnergy: data.metrics.avg_energy,
                },
              ];
              // Mantém os últimos 100 pontos para histórico fluido
              return updated.length > 100 ? updated.slice(updated.length - 100) : updated;
            });
          }
        } catch (err) {
          console.error('Erro ao processar mensagem WebSocket:', err);
        }
      };

      socket.onclose = () => {
        setConnected(false);
        // Tenta reconectar a cada 2 segundos
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, 2000);
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch (e) {
      console.error('Falha ao conectar WebSocket:', e);
    }
  }, [wsUrl]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendAction = useCallback((action: string, payload: Record<string, any> = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...payload }));
    }
  }, []);

  const play = useCallback(() => sendAction('start'), [sendAction]);
  const pause = useCallback(() => sendAction('pause'), [sendAction]);
  const step = useCallback(() => sendAction('step'), [sendAction]);
  const reset = useCallback((seed?: number) => sendAction('reset', { seed }), [sendAction]);
  const setSpeed = useCallback((newTps: number) => sendAction('set_speed', { tps: newTps }), [sendAction]);

  return {
    connected,
    status,
    tps,
    organisms,
    foods,
    clusters,
    metrics,
    metricsHistory,
    play,
    pause,
    step,
    reset,
    setSpeed,
    sendAction,
  };
}
