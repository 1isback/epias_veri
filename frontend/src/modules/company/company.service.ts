import { apiClient } from '@/lib/api-client/apiClient';
import { ICompanyService, CompanyOverviewResponse } from './types';

class CompanyService implements ICompanyService {
  async getOverview(companyId: string): Promise<CompanyOverviewResponse> {
    const response = await apiClient.get<unknown, CompanyOverviewResponse>(`/companies/${companyId}/overview`);
    return response;
  }
}

export const companyService = new CompanyService();
