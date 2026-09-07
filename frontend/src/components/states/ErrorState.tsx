import React from 'react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ 
  title = 'Something went wrong', 
  message = 'We encountered an error while loading this data.',
  onRetry 
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full p-8 text-center space-y-3">
      <div className="w-10 h-10 rounded-full bg-danger/10 flex items-center justify-center mb-2">
        <span className="text-danger font-bold text-xl">!</span>
      </div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="text-xs text-muted-foreground max-w-xs">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-secondary text-secondary-foreground text-xs font-semibold rounded border border-border hover:bg-secondary/80 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
