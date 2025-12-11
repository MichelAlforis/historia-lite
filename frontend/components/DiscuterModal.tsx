'use client';

import { useEffect } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { MessageCircle, AlertTriangle, Clock, ChevronRight } from 'lucide-react';

interface DiscuterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DiscuterModal({ isOpen, onClose }: DiscuterModalProps) {
  const { pendingDilemmas, fetchPendingDilemmas, resolvePlayerDilemma, isLoading } = useGameStore();

  // Fetch dilemmas when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchPendingDilemmas();
    }
  }, [isOpen, fetchPendingDilemmas]);

  if (!isOpen) return null;

  const currentDilemma = pendingDilemmas[0];

  const handleChoice = async (choiceId: number) => {
    if (currentDilemma) {
      await resolvePlayerDilemma(currentDilemma.id, choiceId);
      // If no more dilemmas, close modal
      if (pendingDilemmas.length <= 1) {
        onClose();
      }
    }
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
            Dialogue
          </h2>
          {pendingDilemmas.length > 1 && (
            <p className="text-stone-500 mt-1">
              {pendingDilemmas.length} dialogues en attente
            </p>
          )}
        </div>

        {/* Content */}
        <div className="px-8 pb-8">
          {!currentDilemma ? (
            <div className="text-center py-12">
              <div className="mb-4 flex justify-center">
                <MessageCircle className="w-16 h-16 text-stone-300" />
              </div>
              <p className="text-stone-500 text-lg">
                Aucun dialogue en attente
              </p>
              <p className="text-stone-400 mt-2">
                Avancez dans le temps pour declencher de nouveaux evenements
              </p>
              <button
                onClick={onClose}
                className="mt-6 px-6 py-3 bg-sky-100 text-sky-700 rounded-xl
                  hover:bg-sky-200 transition"
              >
                Fermer
              </button>
            </div>
          ) : (
            <>
              {/* Dilemma title */}
              <div className="bg-amber-50 rounded-2xl p-6 mb-6">
                <h3 className="text-xl font-medium text-stone-800 mb-3">
                  {currentDilemma.title_fr || currentDilemma.title}
                </h3>
                <p className="text-stone-600 leading-relaxed">
                  {currentDilemma.description_fr || currentDilemma.description}
                </p>
              </div>

              {/* Choices */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-stone-500 uppercase tracking-wide">
                  Vos options
                </h4>
                {currentDilemma.choices?.map((choice, index) => (
                  <button
                    key={index}
                    onClick={() => handleChoice(index)}
                    disabled={isLoading}
                    className="w-full text-left p-4 bg-stone-50 rounded-xl
                      hover:bg-sky-50 hover:ring-2 hover:ring-sky-200
                      transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="font-medium text-stone-800 mb-1">
                      {choice.label_fr || choice.label}
                    </div>
                    {(choice.description_fr || choice.description) && (
                      <div className="text-sm text-stone-500 mt-1">
                        {choice.description_fr || choice.description}
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Cancel */}
              <div className="flex justify-end mt-6">
                <button
                  onClick={onClose}
                  className="px-6 py-3 text-stone-600 hover:text-stone-800 transition"
                >
                  Reporter
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
