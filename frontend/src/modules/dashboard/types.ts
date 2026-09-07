export interface Trend {
  value: number;
  isPositive: boolean;
  label?: string;
}

export interface KpiData {
  id: string;
  title: string;
  value: string;
  unit: string;
  trend?: Trend;
  sparklineData?: { time: string; value: number }[];
}

export interface ChartDataPoint {
  time: string;
  mcp: number;
  mcpUsd: number;
  mcpEur: number;
}

export interface ActiveAlert {
  id: string;
  type: string;
  message: string;
  location: string;
  timestamp: string;
  severity: 'critical' | 'warning' | 'info';
  value: string;
}

export interface DashboardAsset {
  id: string;
  name: string;
  type: string;
  currentOutput: number;
  capacityFactor: number;
  status: string;
}

export interface InterconnectorData {
  id: string;
  name: string;
  value: number;
  max: number;
  isPositive: boolean;
}

export interface DashboardOverviewResponse {
  kpis: KpiData[];
  chartData: ChartDataPoint[];
  alerts: ActiveAlert[];
  assets?: DashboardAsset[];
  interconnectors?: InterconnectorData[];
}

export interface IDashboardService {
  getOverview(): Promise<DashboardOverviewResponse>;
}
