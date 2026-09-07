import { useQuery } from '@tanstack/react-query';
import { companyService } from '../company.service';
import { env } from '@/config/env';

export const companyKeys = {
  all: ['company'] as const,
  overview: (companyId: string) => [...companyKeys.all, 'overview', companyId] as const,
};

export function useCompanyOverview(companyId: string) {
  return useQuery({
    queryKey: companyKeys.overview(companyId),
    queryFn: () => companyService.getOverview(companyId),
    enabled: !!companyId,
    refetchInterval: env.DASHBOARD_REFRESH_INTERVAL,
  });
}
