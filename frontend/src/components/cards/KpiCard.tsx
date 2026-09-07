import React from 'react';
import { TrendBadge } from '../badges/TrendBadge';

interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: { value: string | number; isPositive: boolean };
}

export function KpiCard({ title, value, unit, trend }: KpiCardProps) {
  return (
    <div className="bg-card border border-border p-5 rounded-lg shadow-sm flex flex-col justify-between">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">{title}</h3>
      <div className="flex items-end justify-between mt-2">
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold text-foreground">{value}</span>
          {unit && <span className="text-sm font-medium text-muted-foreground">{unit}</span>}
        </div>
        {trend && (
          <TrendBadge value={trend.value} isPositive={trend.isPositive} />
        )}
      </div>
    </div>
  );
}
