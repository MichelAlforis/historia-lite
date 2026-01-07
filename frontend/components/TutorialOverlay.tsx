'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  ChevronRight,
  ChevronLeft,
  X,
  Target,
  CheckCircle,
  Circle,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

// Tutorial step type
export interface TutorialStep {
  id: string;
  title_fr: string;
  content_fr: string;
  highlight: string | null;
  action_required: string | null;
}

// Tutorial configuration from scenario
export interface TutorialConfig {
  enabled: boolean;
  steps: TutorialStep[];
}

interface TutorialOverlayProps {
  config: TutorialConfig | null;
  currentStep: number;
  onStepComplete: (stepId: string) => void;
  onNext: () => void;
  onPrevious: () => void;
  onSkip: () => void;
  onComplete: () => void;
  // Game state for detecting actions
  selectedCountry: string | null;
  tickCount: number;
}

// Highlight positions for different elements
const HIGHLIGHT_POSITIONS: Record<string, { top: string; left: string; width: string; height: string }> = {
  country_card: { top: '20%', left: '25%', width: '200px', height: '150px' },
  tick_button: { top: '30%', left: '5%', width: '150px', height: '50px' },
  event_log: { top: '15%', left: '70%', width: '25%', height: '400px' },
  global_tension: { top: '3%', left: '60%', width: '150px', height: '40px' },
  relations_panel: { top: '40%', left: '30%', width: '400px', height: '200px' },
  diplomatic_actions: { top: '50%', left: '40%', width: '300px', height: '150px' },
};

export default function TutorialOverlay({
  config,
  currentStep,
  onStepComplete,
  onNext,
  onPrevious,
  onSkip,
  onComplete,
  selectedCountry,
  tickCount,
}: TutorialOverlayProps) {
  const [initialTickCount] = useState(tickCount);
  const [actionCompleted, setActionCompleted] = useState(false);
  const [showPulse, setShowPulse] = useState(true);

  // Don't render if no tutorial or disabled
  if (!config || !config.enabled || !config.steps.length) {
    return null;
  }

  const step = config.steps[currentStep];
  const isLastStep = currentStep === config.steps.length - 1;
  const isFirstStep = currentStep === 0;
  const progress = ((currentStep + 1) / config.steps.length) * 100;

  // Detect action completion
  useEffect(() => {
    if (!step?.action_required) {
      setActionCompleted(true);
      return;
    }

    let completed = false;

    switch (step.action_required) {
      case 'select_country_FRA':
        completed = selectedCountry === 'FRA';
        break;
      case 'advance_tick':
        completed = tickCount > initialTickCount;
        break;
      case 'improve_relation':
        // This would need to track relation changes
        // For now, just allow to proceed after some time
        completed = true;
        break;
      default:
        completed = true;
    }

    setActionCompleted(completed);

    if (completed && step.action_required) {
      onStepComplete(step.id);
    }
  }, [step, selectedCountry, tickCount, initialTickCount, onStepComplete]);

  // Pulse animation toggle
  useEffect(() => {
    const interval = setInterval(() => {
      setShowPulse(prev => !prev);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // Handle next with action check
  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else if (actionCompleted || !step.action_required) {
      onNext();
    }
  };

  // Get highlight style
  const getHighlightStyle = () => {
    if (!step.highlight || !HIGHLIGHT_POSITIONS[step.highlight]) {
      return null;
    }
    return HIGHLIGHT_POSITIONS[step.highlight];
  };

  const highlightStyle = getHighlightStyle();

  return (
    <>
      {/* Dark overlay with cutout */}
      <div className="fixed inset-0 z-[200] pointer-events-none">
        {/* Semi-transparent overlay */}
        <div className="absolute inset-0 bg-black/60" />

        {/* Highlight cutout */}
        {highlightStyle && (
          <div
            className={`absolute border-2 border-sky-400 rounded-lg transition-all duration-500 ${
              showPulse ? 'shadow-[0_0_30px_rgba(56,189,248,0.5)]' : 'shadow-[0_0_15px_rgba(56,189,248,0.3)]'
            }`}
            style={{
              top: highlightStyle.top,
              left: highlightStyle.left,
              width: highlightStyle.width,
              height: highlightStyle.height,
              backgroundColor: 'transparent',
              boxShadow: `0 0 0 9999px rgba(0,0,0,0.6), ${
                showPulse ? '0 0 30px rgba(56,189,248,0.5)' : '0 0 15px rgba(56,189,248,0.3)'
              }`,
            }}
          >
            {/* Arrow pointing to element */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-sky-400">
              <ArrowRight className="w-6 h-6 rotate-90 animate-bounce" />
            </div>
          </div>
        )}
      </div>

      {/* Tutorial card */}
      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-[201] w-full max-w-xl px-4">
        <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
          {/* Progress bar */}
          <div className="h-1 bg-slate-800">
            <div
              className="h-full bg-gradient-to-r from-sky-500 to-cyan-400 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Header */}
          <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-sky-500/20 rounded-lg">
                <BookOpen className="w-5 h-5 text-sky-400" />
              </div>
              <div>
                <span className="text-xs text-slate-400">
                  Etape {currentStep + 1} / {config.steps.length}
                </span>
                <h3 className="font-bold text-white">{step.title_fr}</h3>
              </div>
            </div>
            <button
              onClick={onSkip}
              className="p-2 text-slate-400 hover:text-slate-300 hover:bg-slate-700 rounded-lg transition"
              title="Passer le tutoriel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="px-4 py-4">
            <p className="text-slate-300 leading-relaxed">{step.content_fr}</p>

            {/* Action required indicator */}
            {step.action_required && (
              <div
                className={`mt-3 flex items-center gap-2 text-sm ${
                  actionCompleted ? 'text-green-400' : 'text-amber-400'
                }`}
              >
                {actionCompleted ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Action completee !</span>
                  </>
                ) : (
                  <>
                    <Target className="w-4 h-4 animate-pulse" />
                    <span>Action requise pour continuer</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Footer with navigation */}
          <div className="px-4 py-3 bg-slate-800/30 border-t border-slate-700 flex items-center justify-between">
            {/* Step indicators */}
            <div className="flex items-center gap-1">
              {config.steps.map((_, idx) => (
                <div
                  key={idx}
                  className={`w-2 h-2 rounded-full transition ${
                    idx === currentStep
                      ? 'bg-sky-400'
                      : idx < currentStep
                      ? 'bg-green-400'
                      : 'bg-slate-600'
                  }`}
                />
              ))}
            </div>

            {/* Navigation buttons */}
            <div className="flex items-center gap-2">
              {!isFirstStep && (
                <button
                  onClick={onPrevious}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Precedent
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={!!(step.action_required && !actionCompleted)}
                className={`flex items-center gap-1 px-4 py-1.5 text-sm rounded-lg transition ${
                  step.action_required && !actionCompleted
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : isLastStep
                    ? 'bg-green-600 text-white hover:bg-green-500'
                    : 'bg-sky-600 text-white hover:bg-sky-500'
                }`}
              >
                {isLastStep ? (
                  <>
                    Terminer
                    <Sparkles className="w-4 h-4" />
                  </>
                ) : (
                  <>
                    Suivant
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Tutorial objectives display component
interface TutorialObjectivesProps {
  objectives: Array<{
    id: string;
    name: string;
    description: string;
    completed: boolean;
    progress: number;
  }>;
}

export function TutorialObjectives({ objectives }: TutorialObjectivesProps) {
  if (!objectives.length) return null;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-4">
      <h3 className="font-bold text-white mb-3 flex items-center gap-2">
        <Target className="w-4 h-4 text-sky-400" />
        Objectifs du Tutoriel
      </h3>
      <div className="space-y-2">
        {objectives.map((obj) => (
          <div
            key={obj.id}
            className={`flex items-start gap-2 text-sm ${
              obj.completed ? 'text-green-400' : 'text-slate-300'
            }`}
          >
            {obj.completed ? (
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            ) : (
              <Circle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            )}
            <div>
              <span className="font-medium">{obj.name}</span>
              <p className="text-xs text-slate-500">{obj.description}</p>
              {!obj.completed && obj.progress > 0 && (
                <div className="mt-1 h-1 bg-slate-700 rounded overflow-hidden w-24">
                  <div
                    className="h-full bg-sky-500"
                    style={{ width: `${obj.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
