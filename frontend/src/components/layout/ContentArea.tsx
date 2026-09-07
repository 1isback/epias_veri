import React from 'react';

export function ContentArea({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`p-4 md:p-6 w-full max-w-[1920px] mx-auto ${className}`}>
      {children}
    </div>
  );
}
