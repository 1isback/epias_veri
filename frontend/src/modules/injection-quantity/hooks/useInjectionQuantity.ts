import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { injectionQuantityService } from '../injection-quantity.service';
import { InjectionQuantityFilters, InjectionQuantitySyncRequest } from '../types';

export const injectionQuantityKeys = {
  all: ['injection-quantity'] as const,
  powerplants: (search: string) => [...injectionQuantityKeys.all, 'powerplants', search] as const,
  records: (filters: Required<InjectionQuantityFilters>) => [...injectionQuantityKeys.all, 'records', filters] as const,
};

export function useInjectionQuantityPowerplants(search: string) {
  return useQuery({
    queryKey: injectionQuantityKeys.powerplants(search),
    queryFn: () => injectionQuantityService.listPowerplants(search),
  });
}

export function useInjectionQuantityRecords(filters: InjectionQuantityFilters) {
  const isReady = filters.powerplantId !== null && Boolean(filters.startDate) && Boolean(filters.endDate);
  const completeFilters: Required<InjectionQuantityFilters> = {
    powerplantId: filters.powerplantId ?? 0,
    startDate: filters.startDate,
    endDate: filters.endDate,
  };
  return useQuery({
    queryKey: injectionQuantityKeys.records(completeFilters),
    queryFn: () => injectionQuantityService.list(completeFilters),
    enabled: isReady,
  });
}

export function useSyncInjectionQuantityPowerplants() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => injectionQuantityService.syncPowerplants(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: injectionQuantityKeys.all }),
  });
}

export function useSyncInjectionQuantity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: InjectionQuantitySyncRequest) => injectionQuantityService.sync(request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: injectionQuantityKeys.all }),
  });
}
