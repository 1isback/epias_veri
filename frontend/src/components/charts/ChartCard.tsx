import React from 'react';
import { WidgetContainer } from '../widgets/WidgetContainer';

interface ChartCardProps {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  isLoading?: boolean;
  isError?: boolean;
}

export function ChartCard({ title, actions, children, isLoading, isError }: ChartCardProps) {
  return (
    <WidgetContainer title={title} actions={actions} isLoading={isLoading} isError={isError} className="min-h-[400px]">
      <div className="w-full h-full pb-4">
        {children}
      </div>
    </WidgetContainer>
  );
}
