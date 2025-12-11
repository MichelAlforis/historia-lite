'use client';

import { useState } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { Zap, AlertTriangle, Target, Loader2, Check, X } from 'lucide-react';

interface AgirModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AgirModal({ isOpen, onClose }: AgirModalProps) {
  const { sendPlayerCommand, confirmPlayerCommand, cancelPlayerCommand, pendingCommand, isLoading } = useGameStore();
  const [command, setCommand] = useState('');

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!command.trim()) return;
    await sendPlayerCommand(command);
  };

  const handleConfirm = async () => {
    if (pendingCommand?.command_id) {
      await confirmPlayerCommand(pendingCommand.command_id);
      setCommand('');
      onClose();
    }
  };

  const handleCancel = () => {
    cancelPlayerCommand();
    setCommand('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-stone-900/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="px-8 pt-8 pb-4">
          <h2 className="text-2xl font-light text-stone-800">
            Que voulez-vous faire ?
          </h2>
          <p className="text-stone-500 mt-1">
            Decrivez votre action en langage naturel
          </p>
        </div>

        {/* Content */}
        <div className="px-8 pb-8">
          {!pendingCommand ? (
            <>
              {/* Input */}
              <textarea
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Ex: Imposer des sanctions economiques a la Russie, Signer un accord commercial avec le Japon, Renforcer les defenses de l'OTAN..."
                className="w-full h-40 p-4 bg-stone-50 rounded-2xl border-none resize-none
                  text-stone-800 placeholder-stone-400
                  focus:outline-none focus:ring-2 focus:ring-sky-200"
                disabled={isLoading}
              />

              {/* Actions */}
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={onClose}
                  className="px-6 py-3 text-stone-600 hover:text-stone-800 transition"
                >
                  Annuler
                </button>
                <button
                  onClick={handleSend}
                  disabled={!command.trim() || isLoading}
                  className="px-8 py-3 bg-emerald-100 text-emerald-700 rounded-xl
                    hover:bg-emerald-200 transition font-medium
                    disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Analyse...' : 'Analyser'}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Command interpretation */}
              <div className="bg-stone-50 rounded-2xl p-6 space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-stone-500 uppercase tracking-wide mb-2">
                    Action interpretee
                  </h3>
                  <p className="text-stone-800 text-lg">
                    {pendingCommand.interpreted_as || pendingCommand.interpretation?.action}
                  </p>
                </div>

                {pendingCommand.interpretation?.target_country_id && (
                  <div>
                    <h3 className="text-sm font-medium text-stone-500 uppercase tracking-wide mb-2">
                      Cible
                    </h3>
                    <p className="text-stone-800">
                      {pendingCommand.interpretation.target_country_id}
                    </p>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-medium text-stone-500 uppercase tracking-wide mb-2">
                    Confirmation
                  </h3>
                  <p className="text-stone-600">
                    {pendingCommand.confirmation_message_fr || pendingCommand.confirmation_message}
                  </p>
                </div>
              </div>

              {/* Confirm/Cancel */}
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={handleCancel}
                  className="px-6 py-3 text-stone-600 hover:text-stone-800 transition"
                >
                  Modifier
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={isLoading}
                  className="px-8 py-3 bg-emerald-500 text-white rounded-xl
                    hover:bg-emerald-600 transition font-medium
                    disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Execution...' : 'Confirmer'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
