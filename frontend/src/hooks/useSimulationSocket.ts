import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  CompactOrganism,
  CompactFood,
  WorldMetrics,
  SimulationStateMessage,
  WorldEvent,
  FamilyInfo,
  NestInfo,
  ClanInfo,
  TerritoryZoneInfo,
  SeasonInfo,
  EcologyMetrics,
} from '../types';

export function useSimulationSocket(wsUrl: string = 'ws://localhost:8000/api/simulation/ws') {
  const [connected, setConnected] = useState<boolean>(false);
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false);
  const [status, setStatus] = useState<'RUNNING' | 'PAUSED' | 'STOPPED'>('PAUSED');
  const [tps, setTps] = useState<number>(30);
  const [organisms, setOrganisms] = useState<CompactOrganism[]>([]);
  const [foods, setFoods] = useState<CompactFood[]>([]);
  const [clusters, setClusters] = useState<[number, number][]>([]);
  const [clusterHomes, setClusterHomes] = useState<Record<number, number>>({});
  const [families, setFamilies] = useState<FamilyInfo[]>([]);
  const [nests, setNests] = useState<NestInfo[]>([]);
  const [clans, setClans] = useState<ClanInfo[]>([]);
  const [territories, setTerritories] = useState<TerritoryZoneInfo[]>([]);
  const [season, setSeason] = useState<SeasonInfo | null>(null);
  const [ecology, setEcology] = useState<EcologyMetrics | null>(null);
  const [metrics, setMetrics] = useState<WorldMetrics | null>(null);
  const [events, setEvents] = useState<WorldEvent[]>([]);
  const [metricsHistory, setMetricsHistory] = useState<
    Array<{ tick: number; pop: number; food: number; avgEnergy: number }>
  >([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const retryDelayRef = useRef<number>(1000);

  const connect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
        setIsReconnecting(false);
        retryDelayRef.current = 1000;
      };

      socket.onmessage = (event) => {
        try {
          const data: SimulationStateMessage = JSON.parse(event.data);
          if (data.status) setStatus(data.status);
          if (data.tps) setTps(data.tps);
          if (data.orgs) setOrganisms(data.orgs);
          if (data.foods) setFoods(data.foods);
          if (data.clusters) setClusters(data.clusters);
          if (data.cluster_homes) setClusterHomes(data.cluster_homes);
          if (data.families) setFamilies(data.families);
          if (data.nests) setNests(data.nests);
          if (data.clans) setClans(data.clans);
          if (data.territories) setTerritories(data.territories);
          if (data.season) setSeason(data.season);
          else if (data.metrics?.season) setSeason(data.metrics.season);
          if (data.ecology) setEcology(data.ecology);
          else if (data.metrics?.ecology) setEcology(data.metrics.ecology);
          if (data.events && data.events.length > 0) {
            setEvents((prev) => {
              const combined = [...prev, ...(data.events || [])];
              return combined.slice(-50);
            });
          }
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
              return updated.length > 100 ? updated.slice(updated.length - 100) : updated;
            });
          }
        } catch (err) {
          console.error('Erro ao processar mensagem WebSocket:', err);
        }
      };

      socket.onclose = () => {
        setConnected(false);
        setIsReconnecting(true);
        const delay = retryDelayRef.current;
        retryDelayRef.current = Math.min(delay * 1.5, 3500);
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, delay);
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch (e) {
      console.error('Falha ao conectar WebSocket:', e);
      setIsReconnecting(true);
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
  const spawnFood = useCallback((x: number, y: number) => sendAction('spawn_food', { x, y }), [sendAction]);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (_) {}
    }
    setIsReconnecting(true);
    retryDelayRef.current = 1000;
    connect();
  }, [connect]);

  return {
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
    sendAction,
  };
}
