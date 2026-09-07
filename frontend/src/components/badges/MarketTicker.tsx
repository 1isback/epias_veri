import React from 'react';
import { TrendBadge } from './TrendBadge';

export interface TickerItem {
  symbol: string;
  price: number;
  changePercent: number;
  isPositive: boolean;
}

export function MarketTicker({ data = [] }: { data?: TickerItem[] }) {
  if (data.length === 0) {
    return null;
  }

  return (
    <div className="w-full bg-background border-b border-border py-1.5 px-4 overflow-hidden flex items-center text-xs whitespace-nowrap">
      <div className="flex animate-marquee space-x-8 items-center">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="text-muted-foreground font-medium">{item.symbol}</span>
            <span className="text-foreground font-mono">{item.price.toFixed(2)}</span>
            <TrendBadge value={`${(item.changePercent > 0 ? '+' : '')}${item.changePercent}%`} isPositive={item.isPositive} />
          </div>
        ))}
        {data.map((item, idx) => (
          <div key={`dup-${idx}`} className="flex items-center gap-2">
            <span className="text-muted-foreground font-medium">{item.symbol}</span>
            <span className="text-foreground font-mono">{item.price.toFixed(2)}</span>
            <TrendBadge value={`${(item.changePercent > 0 ? '+' : '')}${item.changePercent}%`} isPositive={item.isPositive} />
          </div>
        ))}
      </div>
    </div>
  );
}
