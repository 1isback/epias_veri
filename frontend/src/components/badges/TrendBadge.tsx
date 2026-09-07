import React from 'react';
import { cn } from '@/lib/utils';

export function TrendBadge({ value, isPositive }: { value: number | string; isPositive: boolean }) {
  return (
    <span className={cn(
      "text-xs font-semibold px-1.5 py-0.5 rounded flex items-center gap-1",
      isPositive ? "text-success" : "text-danger"
    )}>
      {isPositive ? '↑' : '↓'}
      {value}
    </span>
  );
}
