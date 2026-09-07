import React from 'react';
import { cn } from '@/lib/utils';

export function ProgressBar({ value, max = 100, className = '', colorClass = 'bg-success' }: { value: number; max?: number; className?: string; colorClass?: string }) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  return (
    <div className={cn("w-full h-1.5 bg-muted rounded-full overflow-hidden", className)}>
      <div 
        className={cn("h-full rounded-full transition-all duration-500", colorClass)}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
