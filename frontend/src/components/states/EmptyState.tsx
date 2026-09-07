import React from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full p-8 text-center space-y-3">
      <div className="w-12 h-12 rounded-full bg-muted/20 flex items-center justify-center mb-2 border border-border">
        <span className="text-muted-foreground text-xl">?</span>
      </div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="text-xs text-muted-foreground max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <button 
          onClick={onAction}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded hover:bg-primary/90 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
