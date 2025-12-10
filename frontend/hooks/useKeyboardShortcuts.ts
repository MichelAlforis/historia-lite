import { useEffect, useCallback } from 'react';

interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  shortcuts: KeyboardShortcut[];
}

export function useKeyboardShortcuts({
  enabled = true,
  shortcuts,
}: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable
      ) {
        // Only allow Escape in inputs
        if (event.key !== 'Escape') return;
      }

      for (const shortcut of shortcuts) {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    },
    [enabled, shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Common shortcuts for Historia Lite
export function useHistoriaShortcuts({
  onTick,
  onReset,
  onToggleAutoPlay,
  onCloseModal,
  onNavigateTab,
  enabled = true,
}: {
  onTick?: () => void;
  onReset?: () => void;
  onToggleAutoPlay?: () => void;
  onCloseModal?: () => void;
  onNavigateTab?: (direction: 'left' | 'right') => void;
  enabled?: boolean;
}) {
  const shortcuts: KeyboardShortcut[] = [];

  if (onTick) {
    shortcuts.push({
      key: ' ',
      action: onTick,
      description: 'Avancer d\'un an (Espace)',
    });
  }

  if (onReset) {
    shortcuts.push({
      key: 'r',
      ctrl: true,
      action: onReset,
      description: 'Reset (Ctrl+R)',
    });
  }

  if (onToggleAutoPlay) {
    shortcuts.push({
      key: 'p',
      action: onToggleAutoPlay,
      description: 'Play/Pause (P)',
    });
  }

  if (onCloseModal) {
    shortcuts.push({
      key: 'Escape',
      action: onCloseModal,
      description: 'Fermer modal (Esc)',
    });
  }

  if (onNavigateTab) {
    shortcuts.push({
      key: 'ArrowLeft',
      alt: true,
      action: () => onNavigateTab('left'),
      description: 'Onglet precedent (Alt+Gauche)',
    });
    shortcuts.push({
      key: 'ArrowRight',
      alt: true,
      action: () => onNavigateTab('right'),
      description: 'Onglet suivant (Alt+Droite)',
    });
  }

  useKeyboardShortcuts({ enabled, shortcuts });

  return shortcuts;
}

// Help modal content
export const SHORTCUTS_HELP = [
  { keys: 'Espace', description: 'Avancer d\'un an' },
  { keys: 'P', description: 'Play/Pause automatique' },
  { keys: 'Esc', description: 'Fermer le modal actif' },
  { keys: 'Alt + Gauche/Droite', description: 'Naviguer entre onglets' },
  { keys: '1-4', description: 'Aller directement a un onglet' },
];
