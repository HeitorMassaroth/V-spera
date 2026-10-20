import React, { useState, useEffect, useCallback } from 'react';
import { X, Database, Plus, Play, Trash2, Camera, Clock, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

interface ExperimentItem {
  id: string;
  name: string;
  description?: string;
  seed?: number;
  status: string;
  latest_tick: number;
  world_width: number;
  world_height: number;
  created_at?: string;
}

interface ExperimentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExperimentRestored?: () => void;
}

export const ExperimentsModal: React.FC<ExperimentsModalProps> = ({
  isOpen,
  onClose,
  onExperimentRestored,
}) => {
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [newName, setNewName] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchExperiments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/experiments');
      if (res.ok) {
        const json = await res.json();
        setExperiments(json);
      }
    } catch (e) {
      console.error('Falha ao carregar lista de experimentos:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchExperiments();
      setFeedback(null);
    }
  }, [isOpen, fetchExperiments]);

  const handleCreateExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setSaving(true);
    setFeedback(null);
    try {
      const res = await fetch('/api/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName.trim(),
          description: newDescription.trim() || undefined,
        }),
      });

      if (res.ok) {
        setNewName('');
        setNewDescription('');
        setFeedback({ type: 'success', message: 'Ensaio científico salvo no banco SQLite com sucesso!' });
        await fetchExperiments();
      } else {
        const err = await res.json();
        setFeedback({ type: 'error', message: err.detail || 'Falha ao salvar experimento.' });
      }
    } catch {
      setFeedback({ type: 'error', message: 'Erro de conexão ao salvar ensaio.' });
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (id: string) => {
    setFeedback(null);
    try {
      const res = await fetch(`/api/experiments/${id}/restore`, { method: 'POST' });
      if (res.ok) {
        setFeedback({ type: 'success', message: 'Ecossistema restaurado com precisão determinística!' });
        if (onExperimentRestored) onExperimentRestored();
      } else {
        const err = await res.json();
        setFeedback({ type: 'error', message: err.detail || 'Falha ao restaurar experimento.' });
      }
    } catch {
      setFeedback({ type: 'error', message: 'Erro ao enviar requisição de restauração.' });
    }
  };

  const handleSaveCheckpoint = async (id: string) => {
    try {
      const res = await fetch(`/api/experiments/${id}/snapshots`, { method: 'POST' });
      if (res.ok) {
        setFeedback({ type: 'success', message: 'Novo checkpoint gravado no banco SQLite.' });
        await fetchExperiments();
      }
    } catch {
      setFeedback({ type: 'error', message: 'Falha ao gravar checkpoint.' });
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Tem certeza que deseja excluir permanentemente este ensaio do banco SQLite?')) return;
    try {
      const res = await fetch(`/api/experiments/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setFeedback({ type: 'success', message: 'Experimento removido do SQLite.' });
        await fetchExperiments();
      }
    } catch {
      setFeedback({ type: 'error', message: 'Falha ao excluir experimento.' });
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '640px',
          maxHeight: '85vh',
          backgroundColor: '#0F172A',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '12px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.95)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38BDF8',
              }}
            >
              <Database size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
                Banco de Dados & Ensaios Científicos (SQLite)
              </h3>
              <p style={{ fontSize: '11px', color: '#94A3B8', margin: 0 }}>
                Persistência de snapshots zlib e restauração determinística
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            style={{
              padding: '8px 16px',
              background: feedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              borderBottom: `1px solid ${feedback.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: feedback.type === 'success' ? '#34D399' : '#FCA5A5',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {feedback.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Formulário: Salvar Ensaio Atual */}
        <form
          onSubmit={handleCreateExperiment}
          style={{
            padding: '14px 20px',
            background: 'rgba(30, 41, 59, 0.5)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Salvar Estado Atual no Banco
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="Nome do Ensaio (ex: Pressão Seletiva G3)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              style={{
                flex: 2,
                padding: '8px 12px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: '#F8FAFC',
                fontSize: '12px',
                outline: 'none',
              }}
              required
            />
            <input
              type="text"
              placeholder="Descrição / Hipótese Científica"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              style={{
                flex: 3,
                padding: '8px 12px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: '#F8FAFC',
                fontSize: '12px',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={saving}
              style={{
                padding: '8px 16px',
                background: 'rgba(56, 189, 248, 0.2)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                borderRadius: '6px',
                color: '#38BDF8',
                fontWeight: 700,
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap',
              }}
            >
              {saving ? <RefreshCw size={13} className="animate-spin" /> : <Plus size={13} />}
              <span>Gravar Snapshot</span>
            </button>
          </div>
        </form>

        {/* Lista de Experimentos Gravados */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>
              Ensaios Armazenados ({experiments.length})
            </span>
            <button
              onClick={fetchExperiments}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#38BDF8',
                fontSize: '11px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <RefreshCw size={11} /> Atualizar
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '24px', color: '#64748B', fontSize: '12px' }}>
              Consultando banco SQLite...
            </div>
          ) : experiments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px', color: '#64748B', fontSize: '12px', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '8px' }}>
              Nenhum experimento gravado no banco de dados ainda. Salve o primeiro ensaio acima.
            </div>
          ) : (
            experiments.map((exp) => (
              <div
                key={exp.id}
                style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC' }}>
                      {exp.name}
                    </span>
                    <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.12)', color: '#38BDF8', fontWeight: 700 }}>
                      Ciclo #{exp.latest_tick}
                    </span>
                    {exp.seed && (
                      <span style={{ fontSize: '9px', color: '#94A3B8' }}>
                        Seed: {exp.seed}
                      </span>
                    )}
                  </div>
                  {exp.description && (
                    <p style={{ fontSize: '11px', color: '#94A3B8', margin: '4px 0 0 0' }}>
                      {exp.description}
                    </p>
                  )}
                  <div style={{ fontSize: '9px', color: '#64748B', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={10} />
                    <span>{exp.created_at ? new Date(exp.created_at).toLocaleString() : 'Sem data'}</span>
                    <span>&bull; Dimensões: {exp.world_width}x{exp.world_height}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={() => handleSaveCheckpoint(exp.id)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#E2E8F0',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                    title="Gravar novo ponto de restauração deste experimento"
                  >
                    <Camera size={12} /> Checkpoint
                  </button>

                  <button
                    onClick={() => handleRestore(exp.id)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: '#34D399',
                      fontWeight: 700,
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                    title="Restaurar simulação a partir deste ensaio no banco"
                  >
                    <Play size={12} /> Restaurar
                  </button>

                  <button
                    onClick={() => handleDelete(exp.id)}
                    style={{
                      padding: '6px 8px',
                      borderRadius: '6px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      color: '#F87171',
                      fontSize: '11px',
                      cursor: 'pointer',
                    }}
                    title="Excluir experimento permanentemente"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
