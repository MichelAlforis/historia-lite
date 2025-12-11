'use client';

import { useState, useRef, useEffect } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { COUNTRY_FLAGS } from '@/lib/types';
import { Send, Loader2, ChevronDown, Plus, MessageCircle, Clock, Check, ThumbsUp, ThumbsDown, Minus, Mic } from 'lucide-react';

// Types
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

export default function DialogueDropup({ isOpen, onClose }: DialogueDropupProps) {
  const { world, playerCountryId, pendingDilemmas, resolvePlayerDilemma, isLoading } = useGameStore();

  // State
  const [dialogues, setDialogues] = useState<Dialogue[]>([]);
  const [selectedDialogueId, setSelectedDialogueId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [message, setMessage] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get current year from world
  const currentYear = world?.year || 2025;

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dialogues]);

  // Focus input when in chat mode
  useEffect(() => {
    if (viewMode === 'chat' && isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
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

  if (!isOpen) return null;

  const selectedDialogue = dialogues.find(d => d.id === selectedDialogueId);

  // Filter dialogues by status
  const ongoingDialogues = dialogues.filter(d => d.status === 'ongoing');
  const requestedDialogues = dialogues.filter(d => d.status === 'requested');
  const pastDialogues = dialogues.filter(d => d.status === 'past');

  // Available countries for selection
  const availableCountries = world?.countries.filter(c => c.id !== playerCountryId) || [];

  // Toggle country selection
  const toggleCountry = (countryId: string) => {
    setSelectedCountries(prev =>
      prev.includes(countryId)
        ? prev.filter(id => id !== countryId)
        : [...prev, countryId]
    );
  };

  // Start new chat
  const handleStartNewChat = () => {
    setSelectedCountries([]);
    setViewMode('select-countries');
  };

  // Create dialogue with selected countries
  const handleCreateDialogue = () => {
    if (selectedCountries.length === 0) return;

    const newDialogue: Dialogue = {
      id: `chat-${Date.now()}`,
      title: `Discussion avec ${selectedCountries.map(id => world?.countries.find(c => c.id === id)?.name || id).join(', ')}`,
      date: currentYear,
      status: 'ongoing',
      participants: selectedCountries,
      messages: [],
      attitudes: Object.fromEntries(selectedCountries.map(id => [id, 'neutral' as const]))
    };

    setDialogues(prev => [...prev, newDialogue]);
    setSelectedDialogueId(newDialogue.id);
    setViewMode('chat');
  };

  // Send message
  const handleSendMessage = async () => {
    if (!message.trim() || !selectedDialogueId) return;

    const playerMsg: DialogueMessage = {
      id: `msg-${Date.now()}`,
      senderId: 'player',
      content: message,
      timestamp: new Date()
    };

    // Add player message
    setDialogues(prev => prev.map(d =>
      d.id === selectedDialogueId
        ? { ...d, messages: [...d.messages, playerMsg] }
        : d
    ));

    setMessage('');

    // Simulate AI responses from participants
    const dialogue = dialogues.find(d => d.id === selectedDialogueId);
    if (dialogue && dialogue.participants.length > 0) {
      // Simulate delay for AI thinking
      setTimeout(() => {
        const responderId = dialogue.participants[Math.floor(Math.random() * dialogue.participants.length)];
        const responses = [
          "Nous sommes disposes a discuter de cette proposition.",
          "Cette initiative merite une reflexion approfondie.",
          "Nous avons des reserves concernant cette approche.",
          "Cela pourrait etre benefique pour nos deux nations.",
          "Nous devons consulter nos allies avant de repondre.",
        ];
        const aiMsg: DialogueMessage = {
          id: `msg-${Date.now()}-ai`,
          senderId: responderId,
          content: responses[Math.floor(Math.random() * responses.length)],
          timestamp: new Date()
        };

        setDialogues(prev => prev.map(d =>
          d.id === selectedDialogueId
            ? { ...d, messages: [...d.messages, aiMsg] }
            : d
        ));

        // Update attitude randomly
        const attitudes = ['positive', 'negative', 'neutral'] as const;
        setDialogues(prev => prev.map(d =>
          d.id === selectedDialogueId
            ? { ...d, attitudes: { ...d.attitudes, [responderId]: attitudes[Math.floor(Math.random() * 3)] } }
            : d
        ));
      }, 1000);
    }
  };

  // Give floor to specific country
  const handleGiveFloor = (countryId: string) => {
    if (!selectedDialogueId) return;

    const country = world?.countries.find(c => c.id === countryId);
    const responses = [
      `${country?.name || countryId} prend la parole: Nous apprecions cette opportunite de dialogue.`,
      `${country?.name || countryId} declare: Notre position reste ferme sur ce sujet.`,
      `${country?.name || countryId} affirme: Nous sommes ouverts a des compromis.`,
    ];

    const aiMsg: DialogueMessage = {
      id: `msg-${Date.now()}-floor`,
      senderId: countryId,
      content: responses[Math.floor(Math.random() * responses.length)],
      timestamp: new Date()
    };

    setDialogues(prev => prev.map(d =>
      d.id === selectedDialogueId
        ? { ...d, messages: [...d.messages, aiMsg] }
        : d
    ));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
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
  };

  // Attitude icon
  const AttitudeIcon = ({ attitude }: { attitude: 'positive' | 'negative' | 'neutral' }) => {
    if (attitude === 'positive') return <ThumbsUp className="w-3 h-3 text-emerald-500" />;
    if (attitude === 'negative') return <ThumbsDown className="w-3 h-3 text-rose-500" />;
    return <Minus className="w-3 h-3 text-stone-400" />;
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-30"
        onClick={onClose}
      />

      {/* Drop-up panel */}
      <div className="fixed bottom-16 left-1/2 -translate-x-1/2 z-40 w-full max-w-2xl">
        <div className="bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden mx-4">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-stone-100">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-sky-500" />
              <span className="text-xs font-medium text-stone-500 uppercase tracking-wide">Dialogues</span>
              {ongoingDialogues.length > 0 && (
                <span className="px-1.5 py-0.5 bg-sky-100 text-sky-600 rounded text-xs">
                  {ongoingDialogues.length}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-stone-100 rounded-lg transition"
            >
              <ChevronDown className="w-4 h-4 text-stone-400" />
            </button>
          </div>

          {/* Content - 2 columns */}
          <div className="flex h-80">
            {/* Sidebar */}
            <div className="w-48 border-r border-stone-100 bg-stone-50 overflow-y-auto">
              {/* Start new chat button */}
              <button
                onClick={handleStartNewChat}
                className="w-full flex items-center gap-2 px-3 py-2 text-sky-600 hover:bg-sky-50 transition text-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Nouvelle discussion</span>
              </button>

              {/* Ongoing */}
              {ongoingDialogues.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    En cours
                  </div>
                  {ongoingDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => { setSelectedDialogueId(d.id); setViewMode('chat'); }}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-sky-500' : ''
                      }`}
                    >
                      <div className="text-sm text-stone-700 truncate">{d.title}</div>
                      <div className="text-xs text-stone-400">{d.date}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Requested */}
              {requestedDialogues.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    Demande
                  </div>
                  {requestedDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => { setSelectedDialogueId(d.id); setViewMode('chat'); }}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-amber-500' : ''
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-amber-500" />
                        <span className="text-sm text-stone-700 truncate">{d.title}</span>
                      </div>
                      <div className="text-xs text-stone-400">{d.date}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Past */}
              {pastDialogues.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-stone-500 uppercase tracking-wide bg-stone-100">
                    Passe
                  </div>
                  {pastDialogues.map(d => (
                    <button
                      key={d.id}
                      onClick={() => { setSelectedDialogueId(d.id); setViewMode('chat'); }}
                      className={`w-full text-left px-3 py-2 hover:bg-white transition ${
                        selectedDialogueId === d.id ? 'bg-white border-l-2 border-stone-400' : ''
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        <Check className="w-3 h-3 text-stone-400" />
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
                <div className="flex-1 flex items-center justify-center text-stone-400 text-sm">
                  Selectionnez un dialogue ou commencez une nouvelle discussion
                </div>
              )}

              {viewMode === 'select-countries' && (
                <div className="flex-1 flex flex-col p-4">
                  <h3 className="text-sm font-medium text-stone-700 mb-3">
                    Selectionnez les pays participants
                  </h3>
                  <div className="flex-1 overflow-y-auto">
                    <div className="grid grid-cols-2 gap-2">
                      {availableCountries.map(country => (
                        <button
                          key={country.id}
                          onClick={() => toggleCountry(country.id)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                            selectedCountries.includes(country.id)
                              ? 'bg-sky-100 text-sky-700 ring-2 ring-sky-300'
                              : 'bg-white hover:bg-stone-100 text-stone-700'
                          }`}
                        >
                          <span className="text-lg">{COUNTRY_FLAGS[country.id] || '🏳️'}</span>
                          <span className="truncate">{country.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-4 pt-3 border-t border-stone-200">
                    <button
                      onClick={() => setViewMode('list')}
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
                      <div className="flex items-center gap-3 flex-wrap">
                        {selectedDialogue.participants.map(countryId => {
                          const country = world?.countries.find(c => c.id === countryId);
                          const attitude = selectedDialogue.attitudes[countryId] || 'neutral';
                          return (
                            <button
                              key={countryId}
                              onClick={() => handleGiveFloor(countryId)}
                              className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-stone-50 hover:bg-stone-100 transition"
                              title={`Donner la parole a ${country?.name || countryId}`}
                            >
                              <span className="text-lg">{COUNTRY_FLAGS[countryId] || '🏳️'}</span>
                              <span className="text-xs text-stone-600">{country?.name || countryId}</span>
                              <AttitudeIcon attitude={attitude} />
                              <Mic className="w-3 h-3 text-stone-400" />
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
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
                                <span>{COUNTRY_FLAGS[msg.senderId] || '🏳️'}</span>
                                <span>{country?.name || msg.senderId}</span>
                              </div>
                            )}
                            {msg.content}
                          </div>
                        </div>
                      );
                    })}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="p-3 border-t border-stone-100 bg-white">
                    <div className="flex items-center gap-2">
                      <input
                        ref={inputRef}
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ecrivez votre message..."
                        className="flex-1 px-3 py-2 bg-stone-50 rounded-xl border-none text-sm
                          text-stone-800 placeholder-stone-400
                          focus:outline-none focus:ring-2 focus:ring-sky-200"
                        disabled={isLoading}
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={!message.trim() || isLoading}
                        className="p-2 bg-sky-500 text-white rounded-xl
                          hover:bg-sky-600 transition
                          disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                      </button>
                    </div>
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
