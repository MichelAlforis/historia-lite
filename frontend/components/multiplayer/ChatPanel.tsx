'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useMultiplayerStore } from '@/stores/multiplayerStore';

interface ChatPanelProps {
  className?: string;
}

export default function ChatPanel({ className = '' }: ChatPanelProps) {
  const {
    chatMessages,
    currentLobby,
    playerId,
    sendChatMessage,
    markMessagesRead,
  } = useMultiplayerStore();

  const [message, setMessage] = useState('');
  const [recipientId, setRecipientId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Mark messages as read when component is visible
  useEffect(() => {
    markMessagesRead();
  }, [markMessagesRead, chatMessages]);

  const handleSend = useCallback(() => {
    if (!message.trim()) return;

    sendChatMessage(message.trim(), recipientId || undefined);
    setMessage('');
    setRecipientId(null);
    inputRef.current?.focus();
  }, [message, recipientId, sendChatMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const otherPlayers = currentLobby?.players.filter((p) => p.id !== playerId) || [];

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`bg-gray-800 rounded-xl p-4 flex flex-col ${className}`}>
      <h3 className="font-bold mb-4 flex items-center gap-2">
        <span>{'💬'}</span>
        Chat diplomatique
        {chatMessages.length > 0 && (
          <span className="px-2 py-0.5 bg-gray-700 rounded text-xs">
            {chatMessages.length}
          </span>
        )}
      </h3>

      {/* Messages */}
      <div className="flex-1 min-h-[200px] max-h-[300px] overflow-y-auto space-y-2 mb-4 pr-2">
        {chatMessages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <span className="text-2xl block mb-2">{'🤝'}</span>
            <p className="text-sm">Aucun message</p>
            <p className="text-xs mt-1">Commencez les negociations!</p>
          </div>
        ) : (
          chatMessages.map((msg) => {
            const isOwn = msg.player_id === playerId;
            return (
              <div
                key={msg.id}
                className={`${isOwn ? 'ml-8' : 'mr-8'}`}
              >
                <div
                  className={`p-2 rounded-lg ${
                    msg.is_private
                      ? 'bg-purple-900/50 border border-purple-700'
                      : isOwn
                      ? 'bg-blue-900/50'
                      : 'bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className={`font-medium ${isOwn ? 'text-blue-400' : 'text-gray-400'}`}>
                      {isOwn ? 'Vous' : msg.player_name}
                    </span>
                    <span className="text-gray-500 flex items-center gap-1">
                      {msg.is_private && (
                        <span title="Message prive" className="text-purple-400">
                          {'🔒'}
                        </span>
                      )}
                      {formatTime(msg.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm">{msg.content}</p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Private message selector */}
      {otherPlayers.length > 0 && (
        <div className="mb-2">
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setRecipientId(null)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                !recipientId
                  ? 'bg-blue-600'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              Public
            </button>
            {otherPlayers.map((player) => (
              <button
                key={player.id}
                onClick={() => setRecipientId(player.id)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  recipientId === player.id
                    ? 'bg-purple-600'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                {'🔒'} {player.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            recipientId
              ? `Message prive a ${otherPlayers.find((p) => p.id === recipientId)?.name}...`
              : 'Envoyer un message...'
          }
          className={`flex-1 px-3 py-2 rounded-lg border focus:outline-none ${
            recipientId
              ? 'bg-purple-900/30 border-purple-700 focus:border-purple-500'
              : 'bg-gray-700 border-gray-600 focus:border-blue-500'
          }`}
          maxLength={500}
        />
        <button
          onClick={handleSend}
          disabled={!message.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {'📤'}
        </button>
      </div>
    </div>
  );
}
