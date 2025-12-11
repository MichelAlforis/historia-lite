'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { X, Send, Lightbulb, Loader2, Eye, Heart, Sword, TrendingUp, ChevronDown } from 'lucide-react';
import { useGameStore } from '@/stores/gameStore';

// ============================================================================
// Constants (TIER 4: No magic numbers)
// ============================================================================
const MAX_MESSAGE_LENGTH = 1000;
const FOCUS_DELAY_MS = 50;
const MAX_HISTORY_MESSAGES = 6;
const PANEL_WIDTH = 'w-80 sm:w-96';
const API_BASE = process.env.NEXT_PUBLIC_HISTORIA_API_URL || 'http://localhost:8001/api';

// ============================================================================
// Types
// ============================================================================
interface AdvisorMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  personality?: string;
}

interface AdvisorPersonality {
  id: string;
  name_fr: string;
  subtitle_fr: string;
  icon: string;
  color: string;
  description_fr: string;
}

// Personality definitions (matching backend)
const PERSONALITIES: AdvisorPersonality[] = [
  {
    id: 'realist',
    name_fr: 'Le Realiste',
    subtitle_fr: 'Ecole Kissinger',
    icon: 'eye',
    color: 'slate',
    description_fr: 'Pragmatisme froid, interets nationaux avant tout.',
  },
  {
    id: 'idealist',
    name_fr: "L'Idealiste",
    subtitle_fr: 'Ecole Wilsonienne',
    icon: 'heart',
    color: 'sky',
    description_fr: 'Droits de l\'homme, cooperation, soft power.',
  },
  {
    id: 'hawk',
    name_fr: 'Le Faucon',
    subtitle_fr: 'Ecole Neoconservatrice',
    icon: 'sword',
    color: 'red',
    description_fr: 'Force militaire, dissuasion, pas de compromis.',
  },
  {
    id: 'economist',
    name_fr: "L'Economiste",
    subtitle_fr: 'Ecole Liberale',
    icon: 'trending-up',
    color: 'emerald',
    description_fr: 'PIB, commerce, sanctions - tout est calcul.',
  },
];

function getPersonalityIcon(iconName: string) {
  const iconClass = "w-4 h-4";
  switch (iconName) {
    case 'eye': return <Eye className={iconClass} />;
    case 'heart': return <Heart className={iconClass} />;
    case 'sword': return <Sword className={iconClass} />;
    case 'trending-up': return <TrendingUp className={iconClass} />;
    default: return <Lightbulb className={iconClass} />;
  }
}

function getPersonalityColorClasses(color: string) {
  const colors: Record<string, { bg: string; text: string; border: string; hover: string }> = {
    slate: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300', hover: 'hover:bg-slate-200' },
    sky: { bg: 'bg-sky-100', text: 'text-sky-700', border: 'border-sky-300', hover: 'hover:bg-sky-200' },
    red: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300', hover: 'hover:bg-red-200' },
    emerald: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-300', hover: 'hover:bg-emerald-200' },
  };
  return colors[color] || colors.slate;
}

interface AdvisorDropleftProps {
  isOpen: boolean;
  onClose: () => void;
}

// ============================================================================
// Component
// ============================================================================
export default function AdvisorDropleft({ isOpen, onClose }: AdvisorDropleftProps) {
  const { world, playerCountryId, pendingDilemmas, eventHistory } = useGameStore();

  // State
  const [messages, setMessages] = useState<AdvisorMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [selectedPersonality, setSelectedPersonality] = useState<string>('realist');
  const [showPersonalityDropdown, setShowPersonalityDropdown] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const focusTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // ============================================================================
  // TIER 1: Memoized computed values
  // ============================================================================
  const playerCountry = useMemo(() =>
    world?.countries.find(c => c.id === playerCountryId),
    [world, playerCountryId]
  );

  const isInputDisabled = useMemo(() =>
    isThinking || !playerCountryId,
    [isThinking, playerCountryId]
  );

  const isSendDisabled = useMemo(() =>
    !inputValue.trim() || isThinking || !playerCountryId,
    [inputValue, isThinking, playerCountryId]
  );

  const characterCount = useMemo(() =>
    `${inputValue.length}/${MAX_MESSAGE_LENGTH}`,
    [inputValue.length]
  );

  // Quick suggestion buttons
  const suggestions = useMemo(() => [
    'Situation actuelle?',
    'Menaces?',
    'Priorites?',
  ], []);

  // Current personality info
  const currentPersonality = useMemo(() =>
    PERSONALITIES.find(p => p.id === selectedPersonality) || PERSONALITIES[0],
    [selectedPersonality]
  );

  const personalityColors = useMemo(() =>
    getPersonalityColorClasses(currentPersonality.color),
    [currentPersonality]
  );

  // ============================================================================
  // TIER 1: Build context for AI (memoized)
  // ============================================================================
  const buildContext = useCallback(() => {
    if (!playerCountry || !world) return null;

    // Get recent events (last 10)
    const recentEvents = eventHistory.slice(0, 10).map(e => ({
      year: e.year,
      type: e.type,
      description: e.description_fr || e.description,
    }));

    // Get relations summary
    const relations: Record<string, number> = {};
    if (playerCountry.relations) {
      Object.entries(playerCountry.relations).forEach(([countryId, rel]) => {
        const country = world.countries.find(c => c.id === countryId);
        if (country) {
          relations[country.name_fr || country.name] = rel;
        }
      });
    }

    // Find allies and rivals based on relations
    const allies = Object.entries(relations)
      .filter(([, rel]) => rel >= 50)
      .map(([name]) => name);

    const rivals = Object.entries(relations)
      .filter(([, rel]) => rel <= -30)
      .map(([name]) => name);

    return {
      year: world.year,
      player: {
        country: playerCountry.name_fr || playerCountry.name,
        power: playerCountry.power_score,
        economy: playerCountry.economy,
        military: playerCountry.military,
        stability: playerCountry.stability,
        nuclear: playerCountry.nuclear,
        blocs: playerCountry.blocs,
      },
      diplomatic: {
        allies: allies.slice(0, 5),
        rivals: rivals.slice(0, 5),
        at_war: playerCountry.at_war || [],
      },
      dilemmas: pendingDilemmas.map(d => ({
        title: d.title_fr || d.title,
        description: d.description_fr || d.description,
      })),
      recentEvents,
      globalTension: world.global_tension,
    };
  }, [playerCountry, world, eventHistory, pendingDilemmas]);

  // ============================================================================
  // TIER 1: Memoized handlers (prevent re-renders)
  // ============================================================================
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    // TIER 2: Input validation - limit length
    const value = e.target.value.slice(0, MAX_MESSAGE_LENGTH);
    setInputValue(value);
  }, []);

  const sendMessage = useCallback(async () => {
    if (!inputValue.trim() || isThinking || !playerCountryId) return;

    const msgContent = inputValue.trim().slice(0, MAX_MESSAGE_LENGTH);
    const userMessage: AdvisorMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: msgContent,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);

    try {
      const context = buildContext();

      const response = await fetch(`${API_BASE}/ai-advisor/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_id: playerCountryId,
          message: userMessage.content,
          context,
          conversation_history: messages.slice(-MAX_HISTORY_MESSAGES).map(m => ({
            role: m.role,
            content: m.content,
          })),
          personality: selectedPersonality, // Include selected personality
        }),
      });

      if (!response.ok) {
        throw new Error('Erreur de communication avec le conseiller');
      }

      const data = await response.json();

      const assistantMessage: AdvisorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'Je n\'ai pas pu analyser votre question. Pouvez-vous reformuler?',
        timestamp: new Date(),
        personality: data.personality || selectedPersonality,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message to advisor:', error);

      const errorMessage: AdvisorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Desole, je ne suis pas disponible actuellement. Verifiez que le serveur IA est connecte.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  }, [inputValue, isThinking, playerCountryId, buildContext, messages, selectedPersonality]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    } else if (e.key === 'Escape') {
      onClose();
    }
  }, [sendMessage, onClose]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setInputValue(suggestion);
  }, []);

  const handlePersonalitySelect = useCallback((personalityId: string) => {
    setSelectedPersonality(personalityId);
    setShowPersonalityDropdown(false);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowPersonalityDropdown(false);
      }
    };
    if (showPersonalityDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showPersonalityDropdown]);

  // ============================================================================
  // TIER 1: Effects with proper cleanup (memory leaks fix)
  // ============================================================================

  // Auto-scroll to bottom when messages change
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

  // Add welcome message on first open
  useEffect(() => {
    if (isOpen && messages.length === 0 && playerCountry) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Bonjour, je suis votre conseiller strategique pour ${playerCountry.name_fr || playerCountry.name}. Je connais la situation geopolitique actuelle et je suis pret a vous aider. Posez-moi vos questions sur la strategie, la diplomatie, l'economie ou les menaces potentielles.`,
        timestamp: new Date(),
      }]);
    }
  }, [isOpen, messages.length, playerCountry]);

  // ============================================================================
  // Render
  // ============================================================================
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
        role="presentation"
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full ${PANEL_WIDTH} bg-white shadow-xl z-50 flex flex-col
          transform transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="advisor-panel-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b bg-amber-50">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" aria-hidden="true" />
            <span
              id="advisor-panel-title"
              className="font-medium text-stone-800 text-sm sm:text-base"
            >
              Conseiller
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-amber-100 rounded transition-colors"
            aria-label="Fermer le panneau du conseiller"
          >
            <X className="w-5 h-5 text-stone-500" aria-hidden="true" />
          </button>
        </div>

        {/* Personality Selector */}
        <div className="px-3 sm:px-4 py-2 border-b bg-white relative" ref={dropdownRef}>
          <button
            onClick={() => setShowPersonalityDropdown(!showPersonalityDropdown)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border ${personalityColors.border} ${personalityColors.bg} ${personalityColors.hover} transition-colors`}
          >
            <div className="flex items-center gap-2">
              <span className={personalityColors.text}>
                {getPersonalityIcon(currentPersonality.icon)}
              </span>
              <div className="text-left">
                <div className={`text-sm font-medium ${personalityColors.text}`}>
                  {currentPersonality.name_fr}
                </div>
                <div className="text-xs text-stone-500">
                  {currentPersonality.subtitle_fr}
                </div>
              </div>
            </div>
            <ChevronDown className={`w-4 h-4 ${personalityColors.text} transition-transform ${showPersonalityDropdown ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown menu */}
          {showPersonalityDropdown && (
            <div className="absolute left-3 right-3 top-full mt-1 bg-white rounded-lg shadow-lg border border-stone-200 z-10 overflow-hidden">
              {PERSONALITIES.map((personality) => {
                const colors = getPersonalityColorClasses(personality.color);
                const isSelected = personality.id === selectedPersonality;
                return (
                  <button
                    key={personality.id}
                    onClick={() => handlePersonalitySelect(personality.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors
                      ${isSelected ? colors.bg : 'hover:bg-stone-50'}`}
                  >
                    <span className={colors.text}>
                      {getPersonalityIcon(personality.icon)}
                    </span>
                    <div className="flex-1">
                      <div className={`text-sm font-medium ${isSelected ? colors.text : 'text-stone-700'}`}>
                        {personality.name_fr}
                      </div>
                      <div className="text-xs text-stone-500">
                        {personality.description_fr}
                      </div>
                    </div>
                    {isSelected && (
                      <div className={`w-2 h-2 rounded-full ${colors.text.replace('text-', 'bg-')}`} />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Context badge */}
        {playerCountry && (
          <div
            className="px-3 sm:px-4 py-2 bg-stone-50 border-b text-xs text-stone-500"
            role="status"
            aria-label="Contexte du jeu"
          >
            <span className="font-medium">{playerCountry.name_fr || playerCountry.name}</span>
            <span className="mx-2">|</span>
            <span>Annee {world?.year}</span>
            <span className="mx-2 hidden sm:inline">|</span>
            <span className="hidden sm:inline">Puissance: {playerCountry.power_score?.toFixed(0)}</span>
          </div>
        )}

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4"
          role="log"
          aria-live="polite"
          aria-label="Historique de conversation avec le conseiller"
        >
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-2.5 sm:p-3 ${
                  msg.role === 'user'
                    ? 'bg-emerald-100 text-emerald-900'
                    : 'bg-stone-100 text-stone-800'
                }`}
              >
                <p className="text-xs sm:text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs mt-1 opacity-50">
                  {msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Thinking indicator */}
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-stone-100 rounded-lg p-2.5 sm:p-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-amber-500" aria-hidden="true" />
                <span className="text-xs sm:text-sm text-stone-500">Analyse en cours...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-3 sm:p-4 bg-white">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Posez une question..."
              maxLength={MAX_MESSAGE_LENGTH}
              disabled={isInputDisabled}
              autoComplete="off"
              data-lpignore="true"
              data-form-type="other"
              className="flex-1 border border-stone-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent
                disabled:bg-stone-50 disabled:text-stone-400"
              aria-label="Message au conseiller"
              aria-describedby="advisor-char-count"
            />
            <button
              onClick={sendMessage}
              disabled={isSendDisabled}
              className="px-3 sm:px-4 py-2 bg-amber-500 text-white rounded-lg
                hover:bg-amber-600 disabled:bg-stone-300 disabled:cursor-not-allowed
                transition-colors flex items-center gap-1"
              aria-label="Envoyer le message"
            >
              <Send className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          {/* Character count (TIER 2) */}
          {inputValue.length > MAX_MESSAGE_LENGTH * 0.8 && (
            <div
              id="advisor-char-count"
              className={`text-xs mt-1 text-right ${
                inputValue.length >= MAX_MESSAGE_LENGTH ? 'text-rose-500' : 'text-stone-400'
              }`}
            >
              {characterCount}
            </div>
          )}

          {/* Quick suggestions */}
          <div
            className="mt-2 flex flex-wrap gap-1"
            role="group"
            aria-label="Suggestions rapides"
          >
            {suggestions.map(suggestion => (
              <button
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isThinking}
                className="text-xs px-2 py-1 bg-stone-100 hover:bg-stone-200
                  rounded text-stone-600 transition-colors disabled:opacity-50"
                aria-label={`Suggestion: ${suggestion}`}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
