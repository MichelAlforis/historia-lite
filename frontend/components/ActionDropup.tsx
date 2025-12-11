'use client';

import { useState, useRef, useEffect } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { Send, Loader2, Check, X, ChevronDown } from 'lucide-react';

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

export default function ActionDropup({ isOpen, onClose }: ActionDropupProps) {
  const { sendPlayerCommand, confirmPlayerCommand, cancelPlayerCommand, pendingCommand, isLoading } = useGameStore();
  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<ActionMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
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

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!command.trim() || isLoading) return;

    // Add user message
    const userMsg: ActionMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: command,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    const cmd = command;
    setCommand('');

    await sendPlayerCommand(cmd);
  };

  const handleConfirm = async () => {
    if (pendingCommand?.command_id) {
      // Update message status
      setMessages(prev => prev.map(m =>
        m.status === 'pending' ? { ...m, status: 'confirmed' as const } : m
      ));

      await confirmPlayerCommand(pendingCommand.command_id);

      // Add result message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'result',
        content: 'Action executee avec succes',
        timestamp: new Date()
      }]);
    }
  };

  const handleCancel = () => {
    // Update message status
    setMessages(prev => prev.map(m =>
      m.status === 'pending' ? { ...m, status: 'cancelled' as const } : m
    ));
    cancelPlayerCommand();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <>
      {/* Backdrop - click to close */}
      <div
        className="fixed inset-0 z-30"
        onClick={onClose}
      />

      {/* Drop-up panel */}
      <div className="fixed bottom-16 left-1/2 -translate-x-1/2 z-40 w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden mx-4">
          {/* Header with close */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-stone-100">
            <span className="text-xs font-medium text-stone-500 uppercase tracking-wide">Actions</span>
            <button
              onClick={onClose}
              className="p-1 hover:bg-stone-100 rounded-lg transition"
            >
              <ChevronDown className="w-4 h-4 text-stone-400" />
            </button>
          </div>

          {/* Messages feed */}
          <div className="h-64 overflow-y-auto p-3 space-y-2 bg-stone-50">
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
                      >
                        <X className="w-3 h-3" />
                        Annuler
                      </button>
                      <button
                        onClick={handleConfirm}
                        disabled={isLoading}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1
                          bg-emerald-500 text-white rounded-lg text-xs hover:bg-emerald-600 transition
                          disabled:opacity-50"
                      >
                        {isLoading ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Check className="w-3 h-3" />
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
                onChange={(e) => setCommand(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Decrivez votre action..."
                className="flex-1 px-3 py-2 bg-stone-50 rounded-xl border-none text-sm
                  text-stone-800 placeholder-stone-400
                  focus:outline-none focus:ring-2 focus:ring-emerald-200"
                disabled={isLoading || !!pendingCommand}
              />
              <button
                onClick={handleSend}
                disabled={!command.trim() || isLoading || !!pendingCommand}
                className="p-2 bg-emerald-500 text-white rounded-xl
                  hover:bg-emerald-600 transition
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
        </div>
      </div>
    </>
  );
}
