import React from 'react';
import { cn } from '@/lib/utils';

export interface AlertData {
  id: string;
  type: 'danger' | 'warning' | 'success' | 'primary';
  title: string;
  time: string;
  subtitle: string;
  value?: string | number;
}

export function AlertList({ alerts }: { alerts: AlertData[] }) {
  return (
    <div className="flex flex-col divide-y divide-border h-full overflow-y-auto">
      {alerts.map((alert) => (
        <div key={alert.id} className="p-3.5 flex items-start gap-3 hover:bg-muted/10 transition-colors cursor-default">
          <div className={cn(
            "w-2 h-2 mt-1.5 rounded-full flex-shrink-0 shadow-[0_0_8px_rgba(0,0,0,0.5)]",
            alert.type === 'danger' && "bg-danger shadow-danger/50",
            alert.type === 'warning' && "bg-warning shadow-warning/50",
            alert.type === 'success' && "bg-success shadow-success/50",
            alert.type === 'primary' && "bg-primary shadow-primary/50"
          )} />
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start">
              <p className="text-sm font-semibold text-foreground truncate">{alert.title}</p>
              <span className="text-xs text-muted-foreground flex-shrink-0 ml-2 font-medium">{alert.time}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1.5 truncate">{alert.subtitle}</p>
          </div>
          {alert.value && (
            <div className={cn(
              "text-xs font-mono font-bold flex-shrink-0 mt-0.5",
              alert.type === 'danger' && "text-danger",
              alert.type === 'warning' && "text-warning"
            )}>
              {alert.value}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
