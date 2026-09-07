import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../dashboard.service';
import { env } from '@/config/env';

export const dashboardKeys = {
  all: ['dashboard'] as const,
  overview: () => [...dashboardKeys.all, 'overview'] as const,
};

export function useDashboardOverview() {
  return useQuery({
    queryKey: dashboardKeys.overview(),
    queryFn: () => dashboardService.getOverview(),
    refetchInterval: env.DASHBOARD_REFRESH_INTERVAL,
  });
}
