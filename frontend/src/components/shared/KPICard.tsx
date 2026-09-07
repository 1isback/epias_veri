import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  trend?: string;
}

export function KPICard({ title, value, trend }: KPICardProps) {
  return (
    <div className="p-4 border rounded shadow-sm bg-white">
      <h3 className="text-sm text-gray-500 font-medium">{title}</h3>
      <p className="text-2xl font-bold mt-2">{value}</p>
      {trend && <span className="text-xs text-green-500 mt-1 block">{trend}</span>}
    </div>
  );
}
