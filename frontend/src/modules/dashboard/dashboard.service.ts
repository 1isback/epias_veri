import { apiClient } from '@/lib/api-client/apiClient';
import { IDashboardService, DashboardOverviewResponse } from './types';

class DashboardService implements IDashboardService {
  async getOverview(): Promise<DashboardOverviewResponse> {
    const response = await apiClient.get<unknown, DashboardOverviewResponse>('/dashboard/overview');
    return response;
  }
}

export const dashboardService = new DashboardService();
