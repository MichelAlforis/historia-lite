import { useState, useCallback, useEffect } from 'react';

export interface TutorialStep {
  id: string;
  title_fr: string;
  content_fr: string;
  highlight: string | null;
  action_required: string | null;
}

export interface TutorialConfig {
  enabled: boolean;
  steps: TutorialStep[];
}

export interface TutorialState {
  active: boolean;
  currentStep: number;
  completedSteps: string[];
  skipped: boolean;
}

const TUTORIAL_STORAGE_KEY = 'historia_tutorial_state';

export function useTutorial(config: TutorialConfig | null) {
  const [state, setState] = useState<TutorialState>({
    active: false,
    currentStep: 0,
    completedSteps: [],
    skipped: false,
  });

  // Load state from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(TUTORIAL_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setState(parsed);
      }
    } catch (e) {
      // Ignore localStorage errors
    }
  }, []);

  // Save state to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem(TUTORIAL_STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // Ignore localStorage errors
    }
  }, [state]);

  // Start tutorial
  const startTutorial = useCallback(() => {
    setState({
      active: true,
      currentStep: 0,
      completedSteps: [],
      skipped: false,
    });
  }, []);

  // Go to next step
  const nextStep = useCallback(() => {
    if (!config) return;

    setState((prev) => {
      const newStep = prev.currentStep + 1;
      if (newStep >= config.steps.length) {
        // Tutorial complete
        return {
          ...prev,
          active: false,
          currentStep: config.steps.length - 1,
          completedSteps: config.steps.map((s) => s.id),
        };
      }
      return {
        ...prev,
        currentStep: newStep,
      };
    });
  }, [config]);

  // Go to previous step
  const previousStep = useCallback(() => {
    setState((prev) => ({
      ...prev,
      currentStep: Math.max(0, prev.currentStep - 1),
    }));
  }, []);

  // Skip tutorial
  const skipTutorial = useCallback(() => {
    setState((prev) => ({
      ...prev,
      active: false,
      skipped: true,
    }));
  }, []);

  // Complete tutorial
  const completeTutorial = useCallback(() => {
    if (!config) return;

    setState({
      active: false,
      currentStep: config.steps.length - 1,
      completedSteps: config.steps.map((s) => s.id),
      skipped: false,
    });
  }, [config]);

  // Mark step as completed (for action-based steps)
  const completeStep = useCallback((stepId: string) => {
    setState((prev) => {
      if (prev.completedSteps.includes(stepId)) {
        return prev;
      }
      return {
        ...prev,
        completedSteps: [...prev.completedSteps, stepId],
      };
    });
  }, []);

  // Reset tutorial
  const resetTutorial = useCallback(() => {
    setState({
      active: false,
      currentStep: 0,
      completedSteps: [],
      skipped: false,
    });
    try {
      localStorage.removeItem(TUTORIAL_STORAGE_KEY);
    } catch (e) {
      // Ignore
    }
  }, []);

  // Check if tutorial should auto-start
  const shouldAutoStart = useCallback(() => {
    if (!config?.enabled) return false;
    if (state.skipped) return false;
    if (state.completedSteps.length === config.steps.length) return false;
    return true;
  }, [config, state.skipped, state.completedSteps]);

  // Current step data
  const currentStepData = config?.steps[state.currentStep] || null;

  // Progress percentage
  const progress = config
    ? ((state.currentStep + 1) / config.steps.length) * 100
    : 0;

  return {
    // State
    active: state.active,
    currentStep: state.currentStep,
    completedSteps: state.completedSteps,
    skipped: state.skipped,
    currentStepData,
    progress,

    // Actions
    startTutorial,
    nextStep,
    previousStep,
    skipTutorial,
    completeTutorial,
    completeStep,
    resetTutorial,
    shouldAutoStart,
  };
}
