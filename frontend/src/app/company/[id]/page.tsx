"use client";
import React from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { ContentArea } from '@/components/layout/ContentArea';
import { DashboardLayout } from '@/components/widgets/DashboardLayout';
import { WidgetRow } from '@/components/widgets/WidgetRow';
import { WidgetColumn } from '@/components/widgets/WidgetColumn';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import { KpiCard } from '@/components/cards/KpiCard';
import { AssetCard } from '@/components/cards/AssetCard';
import { ChartCard } from '@/components/charts/ChartCard';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { useCompanyOverview } from '@/modules/company/hooks/useCompany';

import { useParams } from 'next/navigation';

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;
  const { data, isLoading, isError, refetch } = useCompanyOverview(companyId);

  const details = data?.details;
  const assets = data?.assets || [];
  const production = data?.production || [];

  return (
    <AppShell sidebar={<Sidebar />}>
      <PageHeader 
        title={details?.name || 'Loading Company...'} 
        description={details ? `${details.employees} Employees • Founded ${details.foundedYear}` : ''}
      >
        <button 
          onClick={() => refetch()} 
          className="px-4 py-2 bg-secondary text-secondary-foreground text-sm font-semibold rounded-md border border-border hover:bg-secondary/80 transition-colors mr-2"
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
        <button className="px-4 py-2 bg-secondary text-secondary-foreground text-sm font-semibold rounded-md border border-border hover:bg-secondary/80 transition-colors">
          Compare Entity
        </button>
      </PageHeader>

      <ContentArea>
        <DashboardLayout>
          {/* Overview Stats */}
          <WidgetRow>
            <WidgetColumn span={2}>
              <KpiCard title="Total Capacity" value={details ? `${details.totalCapacity} MW` : '-'} />
            </WidgetColumn>
            <WidgetColumn span={2}>
              <KpiCard title="Active Assets" value={assets.length.toString()} />
            </WidgetColumn>
            <WidgetColumn span={2}>
              <KpiCard title="Market Share" value={details ? `${details.marketShare}%` : '-'} trend={{ value: '+0.2%', isPositive: true }} />
            </WidgetColumn>
          </WidgetRow>

          <WidgetRow>
            {/* Production History */}
            <WidgetColumn span={4}>
              <ChartCard title="Historical Production Mix (YTD)" isLoading={isLoading} isError={isError}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={production} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                    <XAxis dataKey="time" stroke="var(--color-muted-foreground)" tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--color-muted-foreground)" tickLine={false} axisLine={false} />
                    <Tooltip cursor={{ fill: 'var(--color-muted)' }} contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)', borderRadius: '8px' }} />
                    <Bar dataKey="nuclear" stackId="a" fill="var(--color-primary)" name="Nuclear" />
                    <Bar dataKey="gas" stackId="a" fill="var(--color-danger)" name="Gas" />
                    <Bar dataKey="wind" stackId="a" fill="var(--color-success)" name="Wind" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </WidgetColumn>

            {/* Asset List */}
            <WidgetColumn span={2}>
              <WidgetContainer title="Generation Assets" className="h-[400px]" isLoading={isLoading} isError={isError}>
                <div className="flex flex-col h-full overflow-y-auto p-2">
                  {assets.map(asset => (
                    <AssetCard 
                      key={asset.id} 
                      asset={{
                        id: asset.id,
                        name: asset.name,
                        type: asset.type,
                        currentOutput: asset.output,
                        capacityFactor: asset.capacity ? (asset.output / asset.capacity) * 100 : 0,
                        status: asset.status
                      }} 
                    />
                  ))}
                </div>
              </WidgetContainer>
            </WidgetColumn>
          </WidgetRow>
        </DashboardLayout>
      </ContentArea>
    </AppShell>
  );
}
