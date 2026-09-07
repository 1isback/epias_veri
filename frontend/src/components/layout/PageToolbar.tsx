import React from 'react';

export function PageToolbar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 px-6 py-2 border-b border-border bg-background">
      {children}
    </div>
  );
}
