import React from 'react';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  // Currently uses standard CSS/Flex Layout.
  // In future "Custom Dashboard" phase, this will be replaced with React-Grid-Layout logic.
  return (
    <div className="flex flex-col gap-4 w-full">
      {children}
    </div>
  );
}
