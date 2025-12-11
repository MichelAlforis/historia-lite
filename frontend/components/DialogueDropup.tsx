'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { COUNTRY_FLAGS } from '@/lib/types';
import { Send, Loader2, ChevronDown, Plus, MessageCircle, Clock, Check, ThumbsUp, ThumbsDown, Minus, Mic } from 'lucide-react';

// ============================================================================
// Constants (TIER 4: No magic numbers)
// ============================================================================
const MAX_MESSAGE_LENGTH = 500;
const FOCUS_DELAY_MS = 50;
const API_BASE = process.env.NEXT_PUBLIC_HISTORIA_API_URL || 'http://localhost:8001/api';

// ============================================================================
// Types
// ============================================================================
interface Dialogue {
  id: string;
  title: string;
  date: number;
  status: 'ongoing' | 'requested' | 'past';
  participants: string[];
  messages: DialogueMessage[];
  attitudes: Record<string, 'positive' | 'negative' | 'neutral'>;
}

interface DialogueMessage {
  id: string;
  senderId: string; // 'player' or country id
  content: string;
  timestamp: Date;
}

interface DialogueDropupProps {
  isOpen: boolean;
  onClose: () => void;
}

type ViewMode = 'list' | 'select-countries' | 'chat';

// ============================================================================
// Component
// ============================================================================
export default function DialogueDropup({ isOpen, onClose }: DialogueDropupProps) {
  const { world, playerCountryId, pendingDilemmas, isLoading } = useGameStore();

  // State
  const [dialogues, setDialogues] = useState<Dialogue[]>([]);
  const [selectedDialogueId, setSelectedDialogueId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [isAIThinking, setIsAIThinking] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const focusTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get current year from world
  const currentYear = world?.year || 2025;

  // ============================================================================
  // TIER 1: Memoized computed values
  // ============================================================================
  const selectedDialogue = useMemo(() =>
    dialogues.find(d => d.id === selectedDialogueId),
    [dialogues, selectedDialogueId]
  );

  const ongoingDialogues = useMemo(() =>
    dialogues.filter(d => d.status === 'ongoing'),
    [dialogues]
  );

  const requestedDialogues = useMemo(() =>
    dialogues.filter(d => d.status === 'requested'),
    [dialogues]
  );

  const pastDialogues = useMemo(() =>
    dialogues.filter(d => d.status === 'past'),
    [dialogues]
  );

  const availableCountries = useMemo(() =>
    world?.countries.filter(c => c.id !== playerCountryId) || [],
    [world, playerCountryId]
  );

  const isInputDisabled = useMemo(() =>
    isLoading || isAIThinking,
    [isLoading, isAIThinking]
  );

  const isSendDisabled = useMemo(() =>
    !message.trim() || isLoading || isAIThinking,
    [message, isLoading, isAIThinking]
  );

  // ============================================================================
  // TIER 1.3: Real AI API call
  // ============================================================================
  const callDiplomaticAI = useCallback(async (
    targetCountryId: string,
    playerMessage: string,
    action: string = 'diplomatic_discussion'
  ): Promise<string> => {
    if (!playerCountryId) return '';

    try {
      const response = await fetch(
        `${API_BASE}/ai-advisor/dialogue/${playerCountryId}/${targetCountryId}?action=${action}`,
        { method: 'GET' }
      );

      if (!response.ok) {
        throw new Error('API error');
      }

      const data = await response.json();
      if (data.success && data.dialogue) {
        return data.dialogue.message || data.dialogue.content || '';
      }

      // Fallback response if API fails
      return `La délégation de ${targetCountryId} prend note de votre message.`;
    } catch (error) {
      console.error('Error calling diplomatic AI:', error);
      return `La délégation de ${targetCountryId} réfléchit à votre proposition.`;
    }
  }, [playerCountryId]);

  // ============================================================================
  // TIER 1: Memoized handlers (prevent re-renders)
  // ============================================================================
  const toggleCountry = useCallback((countryId: string) => {
    setSelectedCountries(prev =>
      prev.includes(countryId)
        ? prev.filter(id => id !== countryId)
        : [...prev, countryId]
    );
  }, []);

  const handleStartNewChat = useCallback(() => {
    setSelectedCountries([]);
    setViewMode('select-countries');
  }, []);

  const handleCreateDialogue = useCallback(() => {
    if (selectedCountries.length === 0) return;

    const countryNames = selectedCountries
      .map(id => world?.countries.find(c => c.id === id)?.name || id)
      .join(', ');

    const newDialogue: Dialogue = {
      id: `chat-${Date.now()}`,
      title: `Discussion avec ${countryNames}`,
      date: currentYear,
      status: 'ongoing',
      participants: selectedCountries,
      messages: [],
      attitudes: Object.fromEntries(selectedCountries.map(id => [id, 'neutral' as const]))
    };

    setDialogues(prev => [...prev, newDialogue]);
    setSelectedDialogueId(newDialogue.id);
    setViewMode('chat');
  }, [selectedCountries, world, currentYear]);

  const handleSendMessage = useCallback(async () => {
    if (!message.trim() || !selectedDialogueId) return;

    const msgContent = message.slice(0, MAX_MESSAGE_LENGTH); // TIER 2: Input validation
    const playerMsg: DialogueMessage = {
      id: `msg-${Date.now()}`,
      senderId: 'player',
      content: msgContent,
      timestamp: new Date()
    };

    // Add player message
    setDialogues(prev => prev.map(d =>
      d.id === selectedDialogueId
        ? { ...d, messages: [...d.messages, playerMsg] }
        : d
    ));

    setMessage('');

    // Get AI response from participant
    const dialogue = dialogues.find(d => d.id === selectedDialogueId);
    if (dialogue && dialogue.participants.length > 0) {
      setIsAIThinking(true);

      try {
        const responderId = dialogue.participants[Math.floor(Math.random() * dialogue.participants.length)];
        const aiResponse = await callDiplomaticAI(responderId, msgContent, 'diplomatic_discussion');

        const aiMsg: DialogueMessage = {
          id: `msg-${Date.now()}-ai`,
          senderId: responderId,
          content: aiResponse,
          timestamp: new Date()
        };

        setDialogues(prev => prev.map(d =>
          d.id === selectedDialogueId
            ? { ...d, messages: [...d.messages, aiMsg] }
            : d
        ));

        // Update attitude based on response sentiment (simple heuristic)
        const positiveWords = ['acceptons', 'accord', 'bienvenu', 'favorable', 'coopération'];
        const negativeWords = ['refusons', 'inacceptable', 'hostile', 'menace', 'sanctions'];

        let newAttitude: 'positive' | 'negative' | 'neutral' = 'neutral';
        const lowerResponse = aiResponse.toLowerCase();
        if (positiveWords.some(word => lowerResponse.includes(word))) {
          newAttitude = 'positive';
        } else if (negativeWords.some(word => lowerResponse.includes(word))) {
          newAttitude = 'negative';
        }

        setDialogues(prev => prev.map(d =>
          d.id === selectedDialogueId
            ? { ...d, attitudes: { ...d.attitudes, [responderId]: newAttitude } }
            : d
        ));
      } finally {
        setIsAIThinking(false);
      }
    }
  }, [message, selectedDialogueId, dialogues, callDiplomaticAI]);

  const handleGiveFloor = useCallback(async (countryId: string) => {
    if (!selectedDialogueId) return;

    setIsAIThinking(true);
    try {
      const aiResponse = await callDiplomaticAI(countryId, 'general_statement', 'general');

      const aiMsg: DialogueMessage = {
        id: `msg-${Date.now()}-floor`,
        senderId: countryId,
        content: aiResponse,
        timestamp: new Date()
      };

      setDialogues(prev => prev.map(d =>
        d.id === selectedDialogueId
          ? { ...d, messages: [...d.messages, aiMsg] }
          : d
      ));
    } finally {
      setIsAIThinking(false);
    }
  }, [selectedDialogueId, callDiplomaticAI]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    // TIER 2: Input validation - limit length
    const value = e.target.value.slice(0, MAX_MESSAGE_LENGTH);
    setMessage(value);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
    if (e.key === 'Escape') {
      if (viewMode !== 'list') {
        setViewMode('list');
      } else {
        onClose();
      }
    }
  }, [handleSendMessage, viewMode, onClose]);

  const handleSelectDialogue = useCallback((id: string) => {
    setSelectedDialogueId(id);
    setViewMode('chat');
  }, []);

  const handleCancelSelection = useCallback(() => {
    setViewMode('list');
  }, []);

  // ============================================================================
  // TIER 1: Effects with proper cleanup (memory leaks fix)
  // ============================================================================

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dialogues]);

  // TIER 1: Focus input when in chat mode (with cleanup)
  useEffect(() => {
    if (viewMode === 'chat' && isOpen && inputRef.current) {
      // Clear any existing timeout
      if (focusTimeoutRef.current) {
        clearTimeout(focusTimeoutRef.current);
      }
      focusTimeoutRef.current = setTimeout(() => {
        inputRef.current?.focus();
      }, FOCUS_DELAY_MS);
    }

    // Cleanup on unmount or when dependencies change
    return () => {
      if (focusTimeoutRef.current) {
        clearTimeout(focusTimeoutRef.current);
        focusTimeoutRef.current = null;
      }
    };
  }, [viewMode, isOpen]);

  // Convert pending dilemmas to dialogues
  useEffect(() => {
    const dilemmaDialogues: Dialogue[] = pendingDilemmas.map(d => ({
      id: `dilemma-${d.id}`,
      title: d.title_fr || d.title || 'Dilemme',
      date: currentYear,
      status: 'ongoing' as const,
      participants: [],
      messages: [{
        id: `msg-${d.id}`,
        senderId: 'system',
        content: d.description_fr || d.description || '',
        timestamp: new Date()
      }],
      attitudes: {}
    }));

    setDialogues(prev => {
      // Keep user-created dialogues and update dilemma dialogues
      const userDialogues = prev.filter(d => !d.id.startsWith('dilemma-'));
      return [...userDialogues, ...dilemmaDialogues];
    });
  }, [pendingDilemmas, currentYear]);

  // ============================================================================
  // TIER 2: Memoized sub-components
  // ============================================================================
  const AttitudeIcon = useCallback(({ attitude }: { attitude: 'positive' | 'negative' | 'neutral' }) => {
    if (attitude === 'positive') return <ThumbsUp className="w-3 h-3 text-emerald-500" aria-label="Attitude positive" />;
    if (attitude === 'negative') return <ThumbsDown className="w-3 h-3 text-rose-500" aria-label="Attitude négative" />;
    return <Minus className="w-3 h-3 text-stone-400" aria-label="Attitude neutre" />;
  }, []);

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
        className="fixed bottom-16 left-1/2 -translate-x-1/2 z-40 w-full max-w-2xl px-4
          sm:max-w-xl md:max-w-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialogue-dropup-title"
      >
        <div className="bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-stone-100">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-sky-500" aria-hidden="true" />
              <span
                id="dialogue-dropup-title"
                className="text-xs font-medium text-stone-500 uppercase tracking-wide"
              >
                Dialogues
              </span>
              {ongoingDialogues.length > 0 && (
                <span className="px-1.5 py-0.5 bg-sky-100 text-sky-600 rounded text-xs">
                  {ongoingDialogues.length}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-stone-100 rounded-lg transition"
              aria-label="Fermer le panneau de dialogues"
            >
              <ChevronDown className="w-4 h-4 text-stone-400" aria-hidden="true" />
            </button>
          </div>

          {/* Content - 2 columns */}
          <div className="flex h-80 sm:h-72 md:h-80">
            {/* Sidebar */}
            <div
              className="w-40 sm:w-44 md:w-48 border-r border-stone-100 bg-stone-50 overflow-y-auto"
              role="navigation"
              aria-label="Liste des dialogues"
            >
              {/* Start new chat button */}
              <button
                onClick={handleStartNewChat}
                className="w-full flex items-center gap-2 px-3 py-2 text-sky-600 hover:bg-sky-50 transition text-sm"
                aria-label="Commencer une nouvelle discussion"
              >
                <Plus className="w-4 h-4" aria-hidden="true" />
                <span>Nouvelle discussion</span>
              </button>

              {/* Ongoing */}
              {ongoingDialogues.length > 0 && (
                <div role="group" aria-label="Dialogues en cours">
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    En cours
                  </div>
                  {ongoingDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => handleSelectDialogue(d.id)}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-sky-500' : ''
                      }`}
                      aria-selected={selectedDialogueId === d.id}
                    >
                      <div className="text-sm text-stone-700 truncate">{d.title}</div>
                      <div className="text-xs text-stone-400">{d.date}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Requested */}
              {requestedDialogues.length > 0 && (
                <div role="group" aria-label="Demandes de dialogue">
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    Demande
                  </div>
                  {requestedDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => handleSelectDialogue(d.id)}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-amber-500' : ''
                      }`}
                      aria-selected={selectedDialogueId === d.id}
                    >
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-amber-500" aria-hidden="true" />
                        <span className="text-sm text-stone-700 truncate">{d.title}</span>
                      </div>
                      <div className="text-xs text-stone-400">{d.date}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Past */}
              {pastDialogues.length > 0 && (
                <div role="group" aria-label="Dialogues passés">
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    Passe
                  </div>
                  {pastDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => handleSelectDialogue(d.id)}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-stone-400' : ''
                      }`}
                      aria-selected={selectedDialogueId === d.id}
                    >
                      <div className="flex items-center gap-1">
                        <Check className="w-3 h-3 text-stone-400" aria-hidden="true" />
                        <span className="text-sm text-stone-500 truncate">{d.title}</span>
                      </div>
                      <div className="text-xs text-stone-400">{d.date}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Empty state */}
              {dialogues.length === 0 && (
                <div className="px-3 py-6 text-center text-stone-400 text-sm">
                  Aucun dialogue
                </div>
              )}
            </div>

            {/* Main content area */}
            <div className="flex-1 flex flex-col bg-stone-50">
              {viewMode === 'list' && !selectedDialogueId && (
                <div className="flex-1 flex items-center justify-center text-stone-400 text-sm p-4 text-center">
                  Selectionnez un dialogue ou commencez une nouvelle discussion
                </div>
              )}

              {viewMode === 'select-countries' && (
                <div className="flex-1 flex flex-col p-4">
                  <h3 className="text-sm font-medium text-stone-700 mb-3">
                    Selectionnez les pays participants
                  </h3>
                  <div className="flex-1 overflow-y-auto">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {availableCountries.map(country => (
                        <button
                          key={country.id}
                          onClick={() => toggleCountry(country.id)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                            selectedCountries.includes(country.id)
                              ? 'bg-sky-100 text-sky-700 ring-2 ring-sky-300'
                              : 'bg-white hover:bg-stone-100 text-stone-700'
                          }`}
                          aria-pressed={selectedCountries.includes(country.id)}
                        >
                          <span className="text-lg" aria-hidden="true">{COUNTRY_FLAGS[country.id] || '🏳️'}</span>
                          <span className="truncate">{country.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-4 pt-3 border-t border-stone-200">
                    <button
                      onClick={handleCancelSelection}
                      className="px-4 py-2 text-stone-600 hover:text-stone-800 transition text-sm"
                    >
                      Annuler
                    </button>
                    <button
                      onClick={handleCreateDialogue}
                      disabled={selectedCountries.length === 0}
                      className="px-4 py-2 bg-sky-500 text-white rounded-lg text-sm
                        hover:bg-sky-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Commencer ({selectedCountries.length})
                    </button>
                  </div>
                </div>
              )}

              {viewMode === 'chat' && selectedDialogue && (
                <>
                  {/* Participants header with attitudes */}
                  {selectedDialogue.participants.length > 0 && (
                    <div className="px-4 py-2 border-b border-stone-200 bg-white">
                      <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                        {selectedDialogue.participants.map(countryId => {
                          const country = world?.countries.find(c => c.id === countryId);
                          const attitude = selectedDialogue.attitudes[countryId] || 'neutral';
                          return (
                            <button
                              key={countryId}
                              onClick={() => handleGiveFloor(countryId)}
                              disabled={isAIThinking}
                              className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-stone-50
                                hover:bg-stone-100 transition disabled:opacity-50"
                              title={`Donner la parole a ${country?.name || countryId}`}
                              aria-label={`Donner la parole a ${country?.name || countryId}`}
                            >
                              <span className="text-base sm:text-lg" aria-hidden="true">
                                {COUNTRY_FLAGS[countryId] || '🏳️'}
                              </span>
                              <span className="text-xs text-stone-600 hidden sm:inline">
                                {country?.name || countryId}
                              </span>
                              <AttitudeIcon attitude={attitude} />
                              <Mic className="w-3 h-3 text-stone-400" aria-hidden="true" />
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Messages */}
                  <div
                    className="flex-1 overflow-y-auto p-3 space-y-2"
                    role="log"
                    aria-live="polite"
                    aria-label="Historique des messages"
                  >
                    {selectedDialogue.messages.length === 0 && (
                      <div className="text-center text-stone-400 text-sm py-8">
                        Commencez la discussion...
                      </div>
                    )}

                    {selectedDialogue.messages.map(msg => {
                      const isPlayer = msg.senderId === 'player';
                      const isSystem = msg.senderId === 'system';
                      const country = !isPlayer && !isSystem
                        ? world?.countries.find(c => c.id === msg.senderId)
                        : null;

                      return (
                        <div
                          key={msg.id}
                          className={`flex ${isPlayer ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                            isPlayer
                              ? 'bg-sky-500 text-white'
                              : isSystem
                              ? 'bg-amber-50 border border-amber-200 text-stone-700'
                              : 'bg-white border border-stone-200 text-stone-700'
                          }`}>
                            {!isPlayer && !isSystem && (
                              <div className="flex items-center gap-1 mb-1 text-xs text-stone-500">
                                <span aria-hidden="true">{COUNTRY_FLAGS[msg.senderId] || '🏳️'}</span>
                                <span>{country?.name || msg.senderId}</span>
                              </div>
                            )}
                            {msg.content}
                          </div>
                        </div>
                      );
                    })}

                    {/* AI thinking indicator */}
                    {isAIThinking && (
                      <div className="flex justify-start">
                        <div className="bg-stone-100 rounded-xl px-3 py-2 flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-sky-500" aria-hidden="true" />
                          <span className="text-sm text-stone-500">Reflexion en cours...</span>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="p-3 border-t border-stone-100 bg-white">
                    <div className="flex items-center gap-2">
                      <input
                        ref={inputRef}
                        type="text"
                        value={message}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        placeholder="Ecrivez votre message..."
                        maxLength={MAX_MESSAGE_LENGTH}
                        className="flex-1 px-3 py-2 bg-stone-50 rounded-xl border-none text-sm
                          text-stone-800 placeholder-stone-400
                          focus:outline-none focus:ring-2 focus:ring-sky-200"
                        disabled={isInputDisabled}
                        aria-label="Message diplomatique"
                        aria-describedby="dialogue-char-count"
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={isSendDisabled}
                        className="p-2 bg-sky-500 text-white rounded-xl
                          hover:bg-sky-600 transition
                          disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label="Envoyer le message"
                      >
                        {isAIThinking ? (
                          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                        ) : (
                          <Send className="w-4 h-4" aria-hidden="true" />
                        )}
                      </button>
                    </div>
                    {/* Character count (TIER 2) */}
                    {message.length > MAX_MESSAGE_LENGTH * 0.8 && (
                      <div
                        id="dialogue-char-count"
                        className={`text-xs mt-1 text-right ${
                          message.length >= MAX_MESSAGE_LENGTH ? 'text-rose-500' : 'text-stone-400'
                        }`}
                      >
                        {message.length}/{MAX_MESSAGE_LENGTH}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
