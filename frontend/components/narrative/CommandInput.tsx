"use client";

/**
 * CommandInput - Cold War Command Center Style
 *
 * Free text input styled as a military command terminal
 */

import React, { useState, useRef, useEffect } from "react";
import { useNarrativeStore } from "@/stores/narrativeStore";

const EXAMPLE_COMMANDS = [
  "Renforcer notre presence militaire en Europe de l'Ouest",
  "Proposer des negociations avec l'URSS sur Cuba",
  "Menacer Moscou de represailles si les missiles ne sont pas retires",
  "Etablir un blocus naval autour de Cuba",
  "Soutenir discretement l'opposition en Europe de l'Est",
  "Organiser un sommet avec Khrouchtchev",
];

export default function CommandInput() {
  const { inputText, setInputText, parseInput, isLoading, player } =
    useNarrativeStore();

  const [showExamples, setShowExamples] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 150) + "px";
    }
  }, [inputText]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    await parseInput();
  };

  const handleExampleClick = (example: string) => {
    setInputText(example);
    setShowExamples(false);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`bg-[#0d1420] border rounded-lg overflow-hidden transition-colors ${
      isFocused ? "border-cyan-500/50" : "border-cyan-900/30"
    }`}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-cyan-900/30 bg-[#0a0e17]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? "bg-amber-500 animate-pulse" : "bg-green-500"}`} />
            <span className="text-xs font-mono tracking-wider text-cyan-400/70 uppercase">
              Terminal de Commande
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className="text-xs font-mono text-slate-500 hover:text-cyan-400 transition-colors"
          >
            {showExamples ? "[MASQUER]" : "[EXEMPLES]"}
          </button>
        </div>
      </div>

      {/* Examples Panel */}
      {showExamples && (
        <div className="px-4 py-3 border-b border-cyan-900/30 bg-[#080c14]">
          <p className="text-xs text-slate-600 mb-2 font-mono">
            &gt; ORDRES SUGGERES:
          </p>
          <div className="space-y-1">
            {EXAMPLE_COMMANDS.map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="w-full text-left text-xs p-2 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/5 rounded font-mono transition-colors"
              >
                &gt; {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <div className="absolute left-4 top-3 text-cyan-500/50 font-mono text-sm">
            &gt;
          </div>
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Entrez vos ordres, Mr. le President..."
            className="w-full bg-transparent border-0 text-slate-200 placeholder-slate-600 resize-none min-h-[80px] p-3 pl-8 font-mono text-sm focus:outline-none focus:ring-0"
            disabled={isLoading}
          />
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-cyan-900/30 bg-[#080c14]">
          <div className="flex items-center justify-between">
            {/* Status */}
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="text-slate-600">
                {inputText.length} chars
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-500">
                Capital: <span className="text-cyan-400">{player.political_capital}</span>
              </span>
            </div>

            {/* Submit */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-600 font-mono hidden sm:inline">
                Ctrl+Enter
              </span>
              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`px-4 py-1.5 rounded text-xs font-mono uppercase tracking-wider transition-all ${
                  !inputText.trim() || isLoading
                    ? "bg-slate-800 text-slate-600 cursor-not-allowed"
                    : "bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                }`}
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 border border-cyan-500/50 border-t-cyan-500 rounded-full animate-spin" />
                    ANALYSE...
                  </span>
                ) : (
                  "EXECUTER"
                )}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
