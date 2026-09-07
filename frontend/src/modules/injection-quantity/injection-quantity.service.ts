import { apiClient } from '@/lib/api-client/apiClient';
import {
  InjectionQuantityFilters,
  InjectionQuantityListResponse,
  InjectionQuantityPowerplant,
  InjectionQuantityService,
  InjectionQuantitySyncRequest,
  InjectionQuantitySyncResponse,
} from './types';

class EpiasInjectionQuantityService implements InjectionQuantityService {
  async syncPowerplants(): Promise<{ synced_count: number }> {
    return apiClient.post<unknown, { synced_count: number }>('/generation/injection-quantity/powerplants/sync');
  }

  async listPowerplants(search?: string): Promise<InjectionQuantityPowerplant[]> {
    return apiClient.get<unknown, InjectionQuantityPowerplant[]>('/generation/injection-quantity/powerplants', {
      params: { search: search || undefined, limit: 500, offset: 0 },
    });
  }

  async sync(request: InjectionQuantitySyncRequest): Promise<InjectionQuantitySyncResponse> {
    return apiClient.post<InjectionQuantitySyncRequest, InjectionQuantitySyncResponse>('/generation/injection-quantity/sync', request);
  }

  async list(filters: Required<InjectionQuantityFilters>): Promise<InjectionQuantityListResponse> {
    return apiClient.get<unknown, InjectionQuantityListResponse>('/generation/injection-quantity', {
      params: {
        powerplant_id: filters.powerplantId,
        start_date: filters.startDate,
        end_date: filters.endDate,
        limit: 10000,
        offset: 0,
      },
    });
  }
}

export const injectionQuantityService = new EpiasInjectionQuantityService();
