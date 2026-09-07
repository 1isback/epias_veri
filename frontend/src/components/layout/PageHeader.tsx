import React from 'react';

export function PageHeader({ title, description, children }: { title: string; description?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col md:flex-row items-start md:items-center justify-between border-b border-border bg-card/30 px-6 py-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground uppercase">{title}</h1>
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      {children && <div className="mt-4 md:mt-0 flex items-center gap-2">{children}</div>}
    </div>
  );
}
