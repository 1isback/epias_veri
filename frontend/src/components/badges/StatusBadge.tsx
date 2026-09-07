import React from 'react';
import { cn } from '@/lib/utils';

export function StatusBadge({ status }: { status: 'ONLINE' | 'OFFLINE' | 'MAINTENANCE' | string }) {
  const isOnline = status === 'ONLINE';
  
  return (
    <span className="flex items-center gap-1.5 text-xs text-muted-foreground uppercase tracking-wider">
      <span className={cn(
        "w-2 h-2 rounded-full",
        isOnline ? "bg-success" : "bg-muted-foreground"
      )} />
      {status}
    </span>
  );
}
