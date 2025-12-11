'use client';

import { useState, useRef, useEffect } from 'react';
import { X, Send, Lightbulb, Loader2 } from 'lucide-react';
import { useGameStore } from '@/stores/gameStore';

interface AdvisorMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface AdvisorDropleftProps {
  isOpen: boolean;
  onClose: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_HISTORIA_API_URL || 'http://localhost:8001/api';

export default function AdvisorDropleft({ isOpen, onClose }: AdvisorDropleftProps) {
  const { world, playerCountryId, pendingDilemmas, eventHistory } = useGameStore();

  const [messages, setMessages] = useState<AdvisorMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get player country data
  const playerCountry = world?.countries.find(c => c.id === playerCountryId);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
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

  // Build context for AI
  const buildContext = () => {
    if (!playerCountry || !world) return null;

    // Get recent events (last 10)
    const recentEvents = eventHistory.slice(0, 10).map(e => ({
      year: e.year,
      type: e.event_type,
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
        gdp: playerCountry.gdp,
        military: playerCountry.military,
        stability: playerCountry.stability,
        nuclear: playerCountry.nuclear_weapons || 0,
        bloc: playerCountry.bloc,
      },
      diplomatic: {
        allies: allies.slice(0, 5),
        rivals: rivals.slice(0, 5),
        wars: playerCountry.wars || [],
      },
      dilemmas: pendingDilemmas.map(d => ({
        title: d.title_fr || d.title,
        description: d.description_fr || d.description,
      })),
      recentEvents,
      globalTension: world.global_tension,
    };
  };

  // Send message to AI
  const sendMessage = async () => {
    if (!inputValue.trim() || isThinking || !playerCountryId) return;

    const userMessage: AdvisorMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
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
          conversation_history: messages.slice(-6).map(m => ({
            role: m.role,
            content: m.content,
          })),
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
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-96 bg-white shadow-xl z-50 flex flex-col
          transform transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-amber-50">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            <span className="font-medium text-stone-800">Conseiller Strategique</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-amber-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-stone-500" />
          </button>
        </div>

        {/* Context badge */}
        {playerCountry && (
          <div className="px-4 py-2 bg-stone-50 border-b text-xs text-stone-500">
            <span className="font-medium">{playerCountry.name_fr || playerCountry.name}</span>
            <span className="mx-2">|</span>
            <span>Annee {world?.year}</span>
            <span className="mx-2">|</span>
            <span>Puissance: {playerCountry.power_score?.toFixed(0)}</span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-emerald-100 text-emerald-900'
                    : 'bg-stone-100 text-stone-800'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs mt-1 opacity-50">
                  {msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Thinking indicator */}
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-stone-100 rounded-lg p-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
                <span className="text-sm text-stone-500">Analyse en cours...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4 bg-white">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Posez une question..."
              disabled={isThinking || !playerCountryId}
              className="flex-1 border border-stone-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent
                disabled:bg-stone-50 disabled:text-stone-400"
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isThinking || !playerCountryId}
              className="px-4 py-2 bg-amber-500 text-white rounded-lg
                hover:bg-amber-600 disabled:bg-stone-300 disabled:cursor-not-allowed
                transition-colors flex items-center gap-1"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Quick suggestions */}
          <div className="mt-2 flex flex-wrap gap-1">
            {[
              'Situation actuelle?',
              'Menaces?',
              'Priorites?',
            ].map(suggestion => (
              <button
                key={suggestion}
                onClick={() => setInputValue(suggestion)}
                disabled={isThinking}
                className="text-xs px-2 py-1 bg-stone-100 hover:bg-stone-200
                  rounded text-stone-600 transition-colors disabled:opacity-50"
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
