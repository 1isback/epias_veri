import React from 'react';
import { LoadingState } from '../states/LoadingState';
import { ErrorState } from '../states/ErrorState';

interface WidgetContainerProps {
  title?: string;
  subtitle?: string;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function WidgetContainer({ title, subtitle, isLoading, isError, onRetry, actions, children, className = '' }: WidgetContainerProps) {
  return (
    <div className={`bg-card text-card-foreground border border-border rounded-lg shadow-sm flex flex-col overflow-hidden h-full ${className}`}>
      {(title || subtitle || actions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div>
            {title && <h3 className="text-sm font-semibold tracking-wide uppercase text-foreground">{title}</h3>}
            {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      
      <div className="flex-1 min-h-0 relative p-4">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState onRetry={onRetry} />
        ) : (
          children
        )}
      </div>
    </div>
  );
}
