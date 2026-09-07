import React from 'react';
import { StatusBadge } from '../badges/StatusBadge';
import { ProgressBar } from '../badges/ProgressBar';

export interface AssetData {
  id: string;
  name: string;
  type: string;
  currentOutput?: number; // Might be optional based on context
  capacityFactor: number;
  status: string;
}

export function AssetCard({ asset }: { asset: AssetData }) {
  return (
    <div className="flex items-center justify-between p-3 border-b border-border last:border-0 hover:bg-muted/5 transition-colors">
      <div className="flex-1 min-w-0 pr-4">
        <h4 className="text-sm font-semibold text-foreground truncate">{asset.name}</h4>
        <p className="text-xs text-muted-foreground mt-1 truncate">{asset.id} • {asset.type}</p>
      </div>
      <div className="w-24 flex-shrink-0 text-right pr-4">
        <p className="text-sm font-mono font-bold">{asset.currentOutput} <span className="text-xs font-sans text-muted-foreground">MW</span></p>
      </div>
      <div className="w-32 flex-shrink-0 flex items-center gap-3 pr-4 hidden md:flex">
        <ProgressBar value={asset.capacityFactor} className="flex-1" />
        <span className="text-xs font-mono text-muted-foreground w-10 text-right">{asset.capacityFactor.toFixed(1)}%</span>
      </div>
      <div className="w-24 flex-shrink-0 flex justify-end">
        <StatusBadge status={asset.status} />
      </div>
    </div>
  );
}
