'use client';

import { useState, useEffect, useCallback } from 'react';
import { COUNTRY_FLAGS } from '@/lib/types';
import {
  listSaves,
  saveGame,
  loadGame,
  deleteSave,
  exportSave,
  SaveMetadata,
} from '@/lib/api';

interface SaveLoadPanelProps {
  currentYear: number;
  onGameLoaded?: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function SaveLoadPanel({
  currentYear,
  onGameLoaded,
  isOpen,
  onClose,
}: SaveLoadPanelProps) {
  const [saves, setSaves] = useState<SaveMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'load' | 'save'>('load');

  // Save form state
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');

  // Confirmation state
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [confirmLoad, setConfirmLoad] = useState<string | null>(null);

  // Load saves list
  const loadSaves = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listSaves();
      setSaves(data.saves);
    } catch (err) {
      console.error('Failed to load saves:', err);
      setError('Impossible de charger les sauvegardes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadSaves();
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, loadSaves]);

  // Handle save game
  const handleSave = async () => {
    if (!saveName.trim()) {
      setError('Veuillez entrer un nom pour la sauvegarde');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await saveGame(saveName.trim(), saveDescription.trim() || undefined);
      setSuccess(result.message);
      setSaveName('');
      setSaveDescription('');
      loadSaves();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to save game:', err);
      setError('Impossible de sauvegarder la partie');
    } finally {
      setLoading(false);
    }
  };

  // Handle load game
  const handleLoad = async (saveId: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await loadGame(saveId);
      setSuccess(result.message);
      setConfirmLoad(null);
      onGameLoaded?.();
      setTimeout(() => {
        setSuccess(null);
        onClose();
      }, 1500);
    } catch (err) {
      console.error('Failed to load game:', err);
      setError('Impossible de charger la partie');
    } finally {
      setLoading(false);
    }
  };

  // Handle delete save
  const handleDelete = async (saveId: string) => {
    try {
      setLoading(true);
      setError(null);
      await deleteSave(saveId);
      setSuccess('Sauvegarde supprimee');
      setConfirmDelete(null);
      loadSaves();
      setTimeout(() => setSuccess(null), 2000);
    } catch (err) {
      console.error('Failed to delete save:', err);
      setError('Impossible de supprimer la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  // Handle export save
  const handleExport = async (saveId: string) => {
    try {
      setLoading(true);
      const data = await exportSave(saveId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `historia-lite-${saveId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setSuccess('Sauvegarde exportee');
      setTimeout(() => setSuccess(null), 2000);
    } catch (err) {
      console.error('Failed to export save:', err);
      setError('Impossible d\'exporter la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  // Format date
  const formatDate = (isoDate: string) => {
    try {
      const date = new Date(isoDate);
      return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoDate;
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden animate-scaleIn"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-blue-900/50 to-gray-700 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{'💾'}</span>
            <div>
              <h2 className="text-xl font-bold">Sauvegardes</h2>
              <p className="text-xs text-gray-400">Annee actuelle: {currentYear}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-700 transition-colors text-gray-400 hover:text-white"
          >
            {'✕'}
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('load')}
            className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-all ${
              activeTab === 'load'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-750 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span>{'📂'}</span>
            Charger ({saves.length})
          </button>
          <button
            onClick={() => setActiveTab('save')}
            className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-all ${
              activeTab === 'save'
                ? 'bg-green-600 text-white'
                : 'bg-gray-750 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span>{'💾'}</span>
            Sauvegarder
          </button>
        </div>

        {/* Messages */}
        {error && (
          <div className="mx-4 mt-4 px-4 py-2 bg-red-900/50 border border-red-500 rounded-lg text-red-300 text-sm">
            {'⚠️'} {error}
          </div>
        )}
        {success && (
          <div className="mx-4 mt-4 px-4 py-2 bg-green-900/50 border border-green-500 rounded-lg text-green-300 text-sm">
            {'✓'} {success}
          </div>
        )}

        {/* Content */}
        <div className="p-4 max-h-[50vh] overflow-y-auto">
          {/* Load Tab */}
          {activeTab === 'load' && (
            <div className="space-y-3">
              {loading && saves.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <span className="animate-spin inline-block text-2xl">{'⏳'}</span>
                  <div className="mt-2">Chargement...</div>
                </div>
              ) : saves.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <span className="text-4xl block mb-2">{'📭'}</span>
                  <div>Aucune sauvegarde disponible</div>
                  <p className="text-xs mt-1">Utilisez l'onglet Sauvegarder pour creer une sauvegarde</p>
                </div>
              ) : (
                saves.map(save => (
                  <div
                    key={save.id}
                    className={`bg-gray-700/50 rounded-lg p-4 border transition-all ${
                      confirmLoad === save.id || confirmDelete === save.id
                        ? 'border-yellow-500'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-white">{save.name}</span>
                          {save.id === 'autosave' && (
                            <span className="px-2 py-0.5 bg-blue-600/30 text-blue-300 text-xs rounded">
                              Auto
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 space-y-1">
                          <div className="flex items-center gap-4">
                            <span>{'📅'} {formatDate(save.created_at)}</span>
                            <span>{'🗓️'} Annee {save.year}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span>{'🌍'} {save.countries_count} pays</span>
                            <span className={
                              save.global_tension >= 70 ? 'text-red-400' :
                              save.global_tension >= 40 ? 'text-yellow-400' :
                              'text-green-400'
                            }>
                              {'⚡'} Tension: {save.global_tension}%
                            </span>
                            {save.player_country && (
                              <span>
                                {'🎮'} {COUNTRY_FLAGS[save.player_country]} {save.player_country}
                              </span>
                            )}
                          </div>
                          {save.description && (
                            <div className="text-gray-500 italic mt-1">{save.description}</div>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col gap-1">
                        {confirmLoad === save.id ? (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleLoad(save.id)}
                              disabled={loading}
                              className="px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-xs font-medium disabled:opacity-50"
                            >
                              Confirmer
                            </button>
                            <button
                              onClick={() => setConfirmLoad(null)}
                              className="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 rounded text-xs"
                            >
                              Annuler
                            </button>
                          </div>
                        ) : confirmDelete === save.id ? (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleDelete(save.id)}
                              disabled={loading}
                              className="px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-xs font-medium disabled:opacity-50"
                            >
                              Supprimer
                            </button>
                            <button
                              onClick={() => setConfirmDelete(null)}
                              className="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 rounded text-xs"
                            >
                              Annuler
                            </button>
                          </div>
                        ) : (
                          <>
                            <button
                              onClick={() => setConfirmLoad(save.id)}
                              disabled={loading}
                              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs font-medium disabled:opacity-50"
                            >
                              {'📂'} Charger
                            </button>
                            <div className="flex gap-1">
                              <button
                                onClick={() => handleExport(save.id)}
                                disabled={loading}
                                className="flex-1 px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-xs disabled:opacity-50"
                                title="Exporter"
                              >
                                {'📤'}
                              </button>
                              <button
                                onClick={() => setConfirmDelete(save.id)}
                                disabled={loading}
                                className="flex-1 px-2 py-1 bg-gray-600 hover:bg-red-600 rounded text-xs disabled:opacity-50"
                                title="Supprimer"
                              >
                                {'🗑️'}
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Save Tab */}
          {activeTab === 'save' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Nom de la sauvegarde *</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder={`Partie ${currentYear}`}
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Description (optionnel)</label>
                <textarea
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  placeholder="Notes sur cette partie..."
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  rows={3}
                  maxLength={500}
                />
              </div>

              <div className="bg-gray-700/30 rounded-lg p-3 text-sm text-gray-400">
                <div className="font-medium text-gray-300 mb-2">Cette sauvegarde inclura:</div>
                <ul className="space-y-1">
                  <li>{'✓'} Etat complet du monde (annee {currentYear})</li>
                  <li>{'✓'} Tous les pays et leurs relations</li>
                  <li>{'✓'} Zones d'influence et bases militaires</li>
                  <li>{'✓'} Historique des evenements</li>
                  <li>{'✓'} Parametres de jeu</li>
                </ul>
              </div>

              <button
                onClick={handleSave}
                disabled={loading || !saveName.trim()}
                className="w-full py-3 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">{'⏳'}</span>
                    Sauvegarde en cours...
                  </>
                ) : (
                  <>
                    <span>{'💾'}</span>
                    Sauvegarder la partie
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-750 border-t border-gray-700 flex items-center justify-between text-xs text-gray-500">
          <span>{saves.length} sauvegarde{saves.length > 1 ? 's' : ''} disponible{saves.length > 1 ? 's' : ''}</span>
          <span>Raccourci: Ctrl+S pour sauvegarder</span>
        </div>
      </div>
    </div>
  );
}
