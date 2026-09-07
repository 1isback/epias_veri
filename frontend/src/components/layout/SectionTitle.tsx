import React from 'react';

export function SectionTitle({ title, subtitle, rightElement }: { title: string; subtitle?: string; rightElement?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-4 mt-6 first:mt-0">
      <div>
        <h2 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">{title}</h2>
        {subtitle && <p className="text-xs text-muted-foreground/70 mt-1">{subtitle}</p>}
      </div>
      {rightElement && <div>{rightElement}</div>}
    </div>
  );
}
