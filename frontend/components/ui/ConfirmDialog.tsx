'use client';

import React from 'react';

export type ConfirmDialogType = 'danger' | 'warning' | 'info';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  type?: ConfirmDialogType;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  details?: React.ReactNode;
}

const TYPE_STYLES: Record<ConfirmDialogType, { bg: string; border: string; icon: string; iconColor: string; confirmBtn: string }> = {
  danger: {
    bg: 'bg-red-950/95',
    border: 'border-red-500/50',
    icon: '!',
    iconColor: 'text-red-400 bg-red-500/20',
    confirmBtn: 'bg-red-600 hover:bg-red-700',
  },
  warning: {
    bg: 'bg-amber-950/95',
    border: 'border-amber-500/50',
    icon: '!',
    iconColor: 'text-amber-400 bg-amber-500/20',
    confirmBtn: 'bg-amber-600 hover:bg-amber-700',
  },
  info: {
    bg: 'bg-blue-950/95',
    border: 'border-blue-500/50',
    icon: '?',
    iconColor: 'text-blue-400 bg-blue-500/20',
    confirmBtn: 'bg-blue-600 hover:bg-blue-700',
  },
};

export function ConfirmDialog({
  isOpen,
  title,
  message,
  type = 'warning',
  confirmText = 'Confirmer',
  cancelText = 'Annuler',
  onConfirm,
  onCancel,
  details,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  const styles = TYPE_STYLES[type];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div
        className={`relative ${styles.bg} ${styles.border} border rounded-xl shadow-2xl max-w-md w-full mx-4 animate-scale-in`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-full ${styles.iconColor} flex items-center justify-center flex-shrink-0`}>
              <span className="text-2xl font-bold">{styles.icon}</span>
            </div>
            <div className="flex-1">
              <h3
                id="confirm-dialog-title"
                className="text-lg font-semibold text-white"
              >
                {title}
              </h3>
              <p className="mt-2 text-slate-300 text-sm">
                {message}
              </p>
            </div>
          </div>

          {/* Details */}
          {details && (
            <div className="mt-4 p-3 bg-slate-800/50 rounded-lg text-sm">
              {details}
            </div>
          )}

          {/* Actions */}
          <div className="mt-6 flex gap-3 justify-end">
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirm}
              className={`px-4 py-2 ${styles.confirmBtn} text-white rounded-lg transition-colors text-sm font-medium`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes scale-in {
          from {
            transform: scale(0.95);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }
        .animate-scale-in {
          animation: scale-in 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
