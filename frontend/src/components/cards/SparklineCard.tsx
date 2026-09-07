"use client";
import React from 'react';
import { ResponsiveContainer, LineChart, Line, YAxis } from 'recharts';
import { TrendBadge } from '../badges/TrendBadge';

interface SparklineCardProps<TData = Record<string, unknown>> {
  title: string;
  value: string | number;
  unit?: string;
  trend?: { value: string | number; isPositive: boolean };
  data: TData[];
  dataKey: string;
}

export function SparklineCard<TData = Record<string, unknown>>({ title, value, unit, trend, data, dataKey }: SparklineCardProps<TData>) {
  const color = trend?.isPositive === false ? 'var(--color-danger)' : 'var(--color-success)';
  
  return (
    <div className="flex flex-col bg-card border border-border p-4 rounded-lg shadow-sm h-[120px]">
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-xs text-muted-foreground uppercase tracking-wide font-medium">{title}</h4>
      </div>
      
      <div className="flex justify-between items-end flex-1">
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-foreground">{value}</span>
            {unit && <span className="text-xs text-muted-foreground font-medium">{unit}</span>}
          </div>
          {trend && (
            <div>
              <TrendBadge value={trend.value} isPositive={trend.isPositive} />
            </div>
          )}
        </div>
        
        <div className="w-24 h-12">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <YAxis domain={['dataMin', 'dataMax']} hide />
              <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
