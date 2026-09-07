import React from 'react';

export function WidgetRow({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  // A row in the dashboard, wrapping widgets in a CSS grid or flexbox
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full ${className}`}>
      {children}
    </div>
  );
}
