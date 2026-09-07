import React from 'react';

export function AppShell({ children, sidebar }: { children: React.ReactNode; sidebar?: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background text-foreground overflow-hidden">
      {sidebar && (
        <aside className="w-64 border-r border-border bg-card flex-shrink-0 hidden md:block">
          {sidebar}
        </aside>
      )}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
