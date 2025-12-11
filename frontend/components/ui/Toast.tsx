'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

const TOAST_ICONS: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

const TOAST_COLORS: Record<ToastType, { bg: string; border: string; text: string }> = {
  success: {
    bg: 'bg-green-900/90',
    border: 'border-green-500',
    text: 'text-green-400',
  },
  error: {
    bg: 'bg-red-900/90',
    border: 'border-red-500',
    text: 'text-red-400',
  },
  warning: {
    bg: 'bg-amber-900/90',
    border: 'border-amber-500',
    text: 'text-amber-400',
  },
  info: {
    bg: 'bg-blue-900/90',
    border: 'border-blue-500',
    text: 'text-blue-400',
  },
};

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const colors = TOAST_COLORS[toast.type];
  const icon = TOAST_ICONS[toast.type];

  return (
    <div
      className={`${colors.bg} ${colors.border} border rounded-lg shadow-lg p-4 min-w-[280px] max-w-[400px] backdrop-blur-sm animate-slide-in`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <span className={`${colors.text} text-xl font-bold flex-shrink-0`}>
          {icon}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium">{toast.title}</p>
          {toast.message && (
            <p className="text-slate-300 text-sm mt-1">{toast.message}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors flex-shrink-0"
          aria-label="Fermer"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, title: string, message?: string, duration = 4000) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast: Toast = { id, type, title, message, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => removeToast(id), duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
      <style jsx global>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </ToastContext.Provider>
  );
}
