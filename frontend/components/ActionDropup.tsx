'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { Send, Loader2, Check, X, ChevronDown } from 'lucide-react';

// ============================================================================
// Constants (TIER 4: No magic numbers)
// ============================================================================
const MAX_MESSAGE_LENGTH = 500;
const FOCUS_DELAY_MS = 50;

// ============================================================================
// Types
// ============================================================================
interface ActionMessage {
  id: string;
  type: 'user' | 'system' | 'result';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'confirmed' | 'cancelled';
}

interface ActionDropupProps {
  isOpen: boolean;
  onClose: () => void;
}

// ============================================================================
// Component
// ============================================================================
export default function ActionDropup({ isOpen, onClose }: ActionDropupProps) {
  const {
    sendPlayerCommand,
    confirmPlayerCommand,
    cancelPlayerCommand,
    pendingCommand,
    isLoading
  } = useGameStore();

  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<ActionMessage[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const focusTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // ============================================================================
  // TIER 1: Memoized handlers (prevent re-renders)
  // ============================================================================
  const handleSend = useCallback(async () => {
    if (!command.trim() || isLoading) return;

    const userMsg: ActionMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: command.slice(0, MAX_MESSAGE_LENGTH), // TIER 2: Input validation
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    const cmd = command;
    setCommand('');

    await sendPlayerCommand(cmd);
  }, [command, isLoading, sendPlayerCommand]);

  const handleConfirm = useCallback(async () => {
    if (pendingCommand?.command_id) {
      setMessages(prev => prev.map(m =>
        m.status === 'pending' ? { ...m, status: 'confirmed' as const } : m
      ));

      await confirmPlayerCommand(pendingCommand.command_id);

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'result',
        content: 'Action executee avec succes',
        timestamp: new Date()
      }]);
    }
  }, [pendingCommand, confirmPlayerCommand]);

  const handleCancel = useCallback(() => {
    setMessages(prev => prev.map(m =>
      m.status === 'pending' ? { ...m, status: 'cancelled' as const } : m
    ));
    cancelPlayerCommand();
  }, [cancelPlayerCommand]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  }, [handleSend, onClose]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    // TIER 2: Input validation - limit length
    const value = e.target.value.slice(0, MAX_MESSAGE_LENGTH);
    setCommand(value);
  }, []);

  // ============================================================================
  // TIER 1: Effects with proper cleanup (memory leaks fix)
  // ============================================================================

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // TIER 1: Focus input when opened (with cleanup)
  useEffect(() => {
    if (isOpen && inputRef.current) {
      // Clear any existing timeout
      if (focusTimeoutRef.current) {
        clearTimeout(focusTimeoutRef.current);
      }
      // Use requestAnimationFrame for more reliable timing
      focusTimeoutRef.current = setTimeout(() => {
        inputRef.current?.focus();
      }, FOCUS_DELAY_MS);
    }

    // Cleanup on unmount or when isOpen changes
    return () => {
      if (focusTimeoutRef.current) {
        clearTimeout(focusTimeoutRef.current);
        focusTimeoutRef.current = null;
      }
    };
  }, [isOpen]);

  // Add pending command to messages when it arrives
  useEffect(() => {
    if (pendingCommand && !messages.find(m => m.id === pendingCommand.command_id)) {
      setMessages(prev => [...prev, {
        id: pendingCommand.command_id || Date.now().toString(),
        type: 'system',
        content: pendingCommand.confirmation_message_fr || pendingCommand.interpreted_as || 'Action en attente de confirmation',
        timestamp: new Date(),
        status: 'pending'
      }]);
    }
  }, [pendingCommand, messages]);

  // ============================================================================
  // TIER 1: Memoized computed values
  // ============================================================================
  const isInputDisabled = useMemo(() =>
    isLoading || !!pendingCommand,
    [isLoading, pendingCommand]
  );

  const isSendDisabled = useMemo(() =>
    !command.trim() || isLoading || !!pendingCommand,
    [command, isLoading, pendingCommand]
  );

  const characterCount = useMemo(() =>
    `${command.length}/${MAX_MESSAGE_LENGTH}`,
    [command.length]
  );

  // ============================================================================
  // Render
  // ============================================================================
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop - click to close */}
      <div
        className="fixed inset-0 z-30"
        onClick={onClose}
        role="presentation"
        aria-hidden="true"
      />

      {/* Drop-up panel */}
      <div
        className="fixed bottom-16 left-1/2 -translate-x-1/2 z-40 w-full max-w-md
          sm:max-w-lg md:max-w-md px-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="action-dropup-title"
      >
        <div className="bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden">
          {/* Header with close */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-stone-100">
            <span
              id="action-dropup-title"
              className="text-xs font-medium text-stone-500 uppercase tracking-wide"
            >
              Actions
            </span>
            <button
              onClick={onClose}
              className="p-1 hover:bg-stone-100 rounded-lg transition"
              aria-label="Fermer le panneau d'actions"
            >
              <ChevronDown className="w-4 h-4 text-stone-400" aria-hidden="true" />
            </button>
          </div>

          {/* Messages feed */}
          <div
            className="h-64 overflow-y-auto p-3 space-y-2 bg-stone-50"
            role="log"
            aria-live="polite"
            aria-label="Historique des actions"
          >
            {messages.length === 0 && (
              <div className="text-center text-stone-400 text-sm py-8">
                Tapez une action ci-dessous...
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                  msg.type === 'user'
                    ? 'bg-emerald-500 text-white'
                    : msg.type === 'result'
                    ? 'bg-sky-100 text-sky-700'
                    : msg.status === 'confirmed'
                    ? 'bg-emerald-100 text-emerald-700'
                    : msg.status === 'cancelled'
                    ? 'bg-stone-200 text-stone-500 line-through'
                    : 'bg-white border border-stone-200 text-stone-700'
                }`}>
                  {msg.content}

                  {/* Confirmation buttons for pending */}
                  {msg.status === 'pending' && pendingCommand && (
                    <div className="flex gap-2 mt-2 pt-2 border-t border-stone-200">
                      <button
                        onClick={handleCancel}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1
                          bg-stone-100 text-stone-600 rounded-lg text-xs hover:bg-stone-200 transition"
                        aria-label="Annuler l'action"
                      >
                        <X className="w-3 h-3" aria-hidden="true" />
                        Annuler
                      </button>
                      <button
                        onClick={handleConfirm}
                        disabled={isLoading}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1
                          bg-emerald-500 text-white rounded-lg text-xs hover:bg-emerald-600 transition
                          disabled:opacity-50"
                        aria-label="Confirmer l'action"
                      >
                        {isLoading ? (
                          <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
                        ) : (
                          <Check className="w-3 h-3" aria-hidden="true" />
                        )}
                        Confirmer
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-stone-100 bg-white">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={command}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Decrivez votre action..."
                maxLength={MAX_MESSAGE_LENGTH}
                className="flex-1 px-3 py-2 bg-stone-50 rounded-xl border-none text-sm
                  text-stone-800 placeholder-stone-400
                  focus:outline-none focus:ring-2 focus:ring-emerald-200"
                disabled={isInputDisabled}
                aria-label="Entrez votre action"
                aria-describedby="char-count"
              />
              <button
                onClick={handleSend}
                disabled={isSendDisabled}
                className="p-2 bg-emerald-500 text-white rounded-xl
                  hover:bg-emerald-600 transition
                  disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Envoyer l'action"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>
            {/* Character count (TIER 2) */}
            {command.length > MAX_MESSAGE_LENGTH * 0.8 && (
              <div
                id="char-count"
                className={`text-xs mt-1 text-right ${
                  command.length >= MAX_MESSAGE_LENGTH ? 'text-rose-500' : 'text-stone-400'
                }`}
              >
                {characterCount}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
