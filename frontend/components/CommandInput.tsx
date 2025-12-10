'use client';

import { useState } from 'react';
import { CommandResponse } from '@/lib/types';
import { sendCommand, confirmCommand } from '@/lib/api';

interface CommandInputProps {
  playerCountryId: string;
  onCommandExecuted?: (response: CommandResponse) => void;
  disabled?: boolean;
}

const COMMAND_SUGGESTIONS = [
  { fr: 'Attaquer la Belgique', en: 'Attack Belgium' },
  { fr: 'Creer un programme spatial Mars', en: 'Create Mars space program' },
  { fr: 'Imposer des sanctions a la Russie', en: 'Impose sanctions on Russia' },
  { fr: 'Proposer une alliance a la France', en: 'Propose alliance with France' },
  { fr: 'Augmenter les impots', en: 'Raise taxes' },
  { fr: 'Moderniser l\'armee', en: 'Modernize military' },
  { fr: 'Developper l\'economie', en: 'Develop economy' },
  { fr: 'Reformer le pays', en: 'Reform the country' },
];

export default function CommandInput({
  playerCountryId,
  onCommandExecuted,
  disabled = false,
}: CommandInputProps) {
  const [command, setCommand] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingCommand, setPendingCommand] = useState<CommandResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || isLoading || disabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await sendCommand(command.trim(), playerCountryId);

      if (response.requires_confirmation && !response.executed) {
        setPendingCommand(response);
      } else {
        onCommandExecuted?.(response);
        setCommand('');
        setPendingCommand(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'envoi de la commande');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!pendingCommand) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await confirmCommand(pendingCommand.command_id, playerCountryId);
      onCommandExecuted?.(response);
      setCommand('');
      setPendingCommand(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la confirmation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setPendingCommand(null);
    setError(null);
  };

  const selectSuggestion = (suggestion: string) => {
    setCommand(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-3">Commande</h3>

      {/* Command Input */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Entrez votre ordre... (ex: attaquer la Belgique)"
            disabled={disabled || isLoading || !!pendingCommand}
            className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />

          {/* Suggestions dropdown */}
          {showSuggestions && !pendingCommand && (
            <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {COMMAND_SUGGESTIONS.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => selectSuggestion(suggestion.fr)}
                  className="w-full px-4 py-2 text-left text-gray-200 hover:bg-gray-600 first:rounded-t-lg last:rounded-b-lg"
                >
                  <span className="text-white">{suggestion.fr}</span>
                  <span className="text-gray-400 text-sm ml-2">({suggestion.en})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {!pendingCommand && (
          <button
            type="submit"
            disabled={disabled || isLoading || !command.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {isLoading ? 'Analyse en cours...' : 'Envoyer'}
          </button>
        )}
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-3 p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Pending Command Confirmation */}
      {pendingCommand && (
        <div className="mt-4 p-4 bg-gray-700 rounded-lg border border-blue-500">
          <h4 className="text-white font-medium mb-2">Confirmation requise</h4>

          <div className="space-y-2 text-sm">
            <p className="text-gray-300">
              <span className="text-gray-400">Commande:</span>{' '}
              {pendingCommand.original_command}
            </p>
            <p className="text-gray-300">
              <span className="text-gray-400">Interprete comme:</span>{' '}
              {pendingCommand.interpreted_as}
            </p>

            {/* Cost preview */}
            {Object.entries(pendingCommand.cost).some(([, v]) => v !== 0) && (
              <div className="mt-2">
                <span className="text-gray-400">Cout:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(pendingCommand.cost).map(([stat, value]) => {
                    if (value === 0) return null;
                    const isNegative = value < 0;
                    return (
                      <span
                        key={stat}
                        className={`px-2 py-1 rounded text-xs ${
                          isNegative ? 'bg-red-900/50 text-red-200' : 'bg-green-900/50 text-green-200'
                        }`}
                      >
                        {stat}: {isNegative ? '' : '+'}{value}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Feasibility */}
            {!pendingCommand.feasible && (
              <div className="mt-2 p-2 bg-yellow-900/50 rounded text-yellow-200 text-sm">
                <span className="font-medium">Non realisable:</span>{' '}
                {pendingCommand.feasibility_reason}
              </div>
            )}

            <p className="text-blue-200 mt-2">
              {pendingCommand.confirmation_message_fr || pendingCommand.confirmation_message}
            </p>
          </div>

          {/* Confirmation buttons */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleConfirm}
              disabled={isLoading || !pendingCommand.feasible}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {isLoading ? 'Execution...' : 'Confirmer'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isLoading}
              className="flex-1 bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Annuler
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
