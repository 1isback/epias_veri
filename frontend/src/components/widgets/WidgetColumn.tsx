import React from 'react';

export function WidgetColumn({ children, span = 1, className = '' }: { children: React.ReactNode; span?: number; className?: string }) {
  // A column wrapper to allow widgets to span multiple grid columns
  const spanClass = {
    1: 'col-span-1',
    2: 'col-span-1 md:col-span-2',
    3: 'col-span-1 md:col-span-3',
    4: 'col-span-1 md:col-span-4',
    5: 'col-span-1 md:col-span-5',
    6: 'col-span-1 md:col-span-6 xl:col-span-6',
  }[span] || 'col-span-1';

  return (
    <div className={`${spanClass} ${className}`}>
      {children}
    </div>
  );
}
