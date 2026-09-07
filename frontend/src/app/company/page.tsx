"use client";
import React from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { ContentArea } from '@/components/layout/ContentArea';
import { EmptyState } from '@/components/states/EmptyState';
import { useRouter } from 'next/navigation';

export default function CompanyIndexPage() {
  const router = useRouter();

  return (
    <AppShell sidebar={<Sidebar />}>
      <PageHeader 
        title="Company Intelligence" 
        description="Select a company to view detailed performance metrics"
      />
      <ContentArea>
        <div className="flex-1 bg-card rounded-lg border border-border shadow-sm flex items-center justify-center">
          <EmptyState 
            title="No Company Selected"
            description="Please select a company from the sidebar or search to view their generation assets, capacity, and market share."
            actionLabel="View Demo Company (EDF-TR)"
            onAction={() => router.push('/company/EDF-TR')}
          />
        </div>
      </ContentArea>
    </AppShell>
  );
}
