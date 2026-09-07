"use client";
import React from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { ContentArea } from '@/components/layout/ContentArea';
import { DashboardLayout } from '@/components/widgets/DashboardLayout';
import { WidgetRow } from '@/components/widgets/WidgetRow';
import { WidgetColumn } from '@/components/widgets/WidgetColumn';
import { MarketTicker } from '@/components/badges/MarketTicker';
import { SparklineCard } from '@/components/cards/SparklineCard';
import { ChartCard } from '@/components/charts/ChartCard';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import { AlertList } from '@/components/alerts/AlertList';
import { AssetCard } from '@/components/cards/AssetCard';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { cn, downloadCsv } from '@/lib/utils';
import { useDashboardOverview } from '@/modules/dashboard/hooks/useDashboard';

import { useAuthStore } from '@/store/useAuthStore';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useDashboardOverview();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();

  // Safely extract data with fallbacks for now
  const kpis = data?.kpis || [];
  const chartData = data?.chartData || [];
  const alerts = data?.alerts || [];
  const assets = data?.assets || [];
  const interconnectors = data?.interconnectors || [];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleExport = () => {
    if (!chartData.length) return;
    downloadCsv(`ptf_${new Date().toISOString().slice(0, 10)}.csv`, [
      { field: 'time', headerName: 'Saat' },
      { field: 'mcp', headerName: 'PTF (TL/MWh)' },
      { field: 'mcpUsd', headerName: 'PTF (USD/MWh)' },
      { field: 'mcpEur', headerName: 'PTF (EUR/MWh)' },
    ], chartData);
  };

  return (
    <AppShell sidebar={<Sidebar />}>
      <MarketTicker />
      <PageHeader 
        title="Command Center" 
        description="GB Grid Overview"
      >
        {user?.is_admin && (
          <Link href="/users" className="px-4 py-2 bg-emerald-600 text-white font-semibold text-sm rounded-md hover:bg-emerald-700 transition-colors">
            Pending Users
          </Link>
        )}
        <button 
          onClick={() => refetch()} 
          className="px-4 py-2 bg-secondary text-secondary-foreground font-semibold text-sm rounded-md border border-border hover:bg-secondary/80 transition-colors"
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
        <button
          onClick={handleExport}
          disabled={!chartData.length}
          className="px-4 py-2 bg-primary text-primary-foreground font-semibold text-sm rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          Export
        </button>
        <button onClick={handleLogout} className="px-4 py-2 bg-danger/10 text-danger font-semibold text-sm rounded-md hover:bg-danger/20 transition-colors ml-4">
          Logout
        </button>
      </PageHeader>

      <ContentArea>
        <DashboardLayout>
          {/* KPI Row */}
          <WidgetRow>
            {kpis.map((kpi, index) => (
              <WidgetColumn span={1} key={kpi.id || index}>
                <SparklineCard 
                  title={kpi.title} 
                  value={kpi.value} 
                  unit={kpi.unit}
                  trend={kpi.trend}
                  data={kpi.sparklineData || []} 
                  dataKey="value"
                />
              </WidgetColumn>
            ))}
            
            {/* If backend fails or returns empty, show loading/error skeletons for KPIs? 
                For now we just map over what we get. If isLoading, we could render 6 skeletons. */}
            {isLoading && !data && Array.from({ length: 6 }).map((_, i) => (
               <WidgetColumn span={1} key={`skeleton-${i}`}>
                 <div className="h-[120px] bg-card/50 border border-border rounded-lg animate-pulse" />
               </WidgetColumn>
            ))}
          </WidgetRow>

          {/* Main Content Row */}
          <WidgetRow>
            {/* Left Column (Charts & Positions) */}
            <WidgetColumn span={4} className="flex flex-col gap-4">
              <ChartCard title="Piyasa Takas Fiyatı (PTF) — Bugün" isLoading={isLoading} isError={isError}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                    <XAxis dataKey="time" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}`} width={40} />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)', borderRadius: '8px' }} formatter={(val: number) => [`${val.toFixed(2)}`, '']} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                    <Line type="monotone" dataKey="mcp" name="PTF (TL/MWh)" stroke="var(--color-primary)" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="mcpUsd" name="PTF (USD/MWh)" stroke="var(--color-success)" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="mcpEur" name="PTF (EUR/MWh)" stroke="var(--color-warning)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Asset Status is theoretically another module, using mock for now */}
              <WidgetContainer title="Asset Status" className="h-[300px]">
                <div className="flex flex-col h-full overflow-y-auto p-2">
                  <div className="flex items-center justify-between p-3 border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider rounded-t-md">
                    <div className="flex-1">Asset</div>
                    <div className="w-24 text-right pr-4">Output</div>
                    <div className="w-32 pr-4 hidden md:block">CAP%</div>
                    <div className="w-24 text-right">Status</div>
                  </div>
                  {assets.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground p-4">
                      No active assets.
                    </div>
                  ) : (
                    assets.map(asset => (
                      <AssetCard key={asset.id} asset={asset} />
                    ))
                  )}
                </div>
              </WidgetContainer>
            </WidgetColumn>

            {/* Right Column (Alerts & Interconnectors) */}
            <WidgetColumn span={2} className="flex flex-col gap-4">
              <WidgetContainer 
                title="Active Alerts" 
                actions={alerts.length > 0 ? <span className="bg-warning/20 text-warning px-2 py-0.5 rounded text-xs font-bold">{alerts.length}</span> : null}
                className="h-[350px]"
                isLoading={isLoading}
                isError={isError}
              >
                <div className="h-full overflow-y-auto">
                  <AlertList alerts={alerts.map(a => ({
                    id: a.id,
                    type: a.severity === 'critical' ? 'danger' : a.severity === 'warning' ? 'warning' : 'primary',
                    title: a.message,
                    time: a.timestamp,
                    subtitle: a.location,
                    value: a.value
                  }))} />
                </div>
              </WidgetContainer>

              <WidgetContainer title="Interconnector Flows" className="h-[350px]">
                <div className="flex flex-col p-4 gap-5 overflow-y-auto h-full">
                  {interconnectors.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground p-4">
                      No interconnector data.
                    </div>
                  ) : (
                    interconnectors.map(conn => (
                      <div key={conn.id} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground font-medium">{conn.name}</span>
                        <div className="flex items-center gap-4 flex-1 justify-end">
                          <div className="w-24 h-1.5 bg-muted rounded-full overflow-hidden flex justify-end">
                            {conn.isPositive && (
                              <div className="h-full bg-success rounded-full" style={{ width: `${(conn.value / conn.max) * 100}%` }} />
                            )}
                            {!conn.isPositive && (
                              <div className="h-full bg-danger rounded-full mr-auto" style={{ width: `${(Math.abs(conn.value) / conn.max) * 100}%` }} />
                            )}
                          </div>
                          <span className={cn("font-mono font-bold w-16 text-right", conn.isPositive ? "text-success" : "text-danger")}>
                            {conn.isPositive ? '+' : ''}{conn.value.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </WidgetContainer>
            </WidgetColumn>
          </WidgetRow>
        </DashboardLayout>
      </ContentArea>
    </AppShell>
  );
}
