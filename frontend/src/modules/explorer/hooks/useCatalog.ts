import { useMutation, useQuery } from '@tanstack/react-query';
import { catalogService, DatasetListFilters } from '../catalog.service';
import { DatasetQueryVars } from '../types';

const FIVE_MIN = 5 * 60 * 1000;
const THIRTY_MIN = 30 * 60 * 1000;

export const catalogKeys = {
  all: ['catalog'] as const,
  categories: ['catalog', 'categories'] as const,
  datasets: (filters: DatasetListFilters) => ['catalog', 'datasets', filters] as const,
  dataset: (id: string) => ['catalog', 'dataset', id] as const,
  lookup: (id: string) => ['catalog', 'lookup', id] as const,
};

export function useCatalogCategories() {
  return useQuery({
    queryKey: catalogKeys.categories,
    queryFn: () => catalogService.getCategories(),
    staleTime: FIVE_MIN,
  });
}

export function useCatalogDatasets(filters: DatasetListFilters) {
  return useQuery({
    queryKey: catalogKeys.datasets(filters),
    queryFn: () => catalogService.listDatasets(filters),
    staleTime: FIVE_MIN,
  });
}

export function useDatasetDetail(id: string | null) {
  return useQuery({
    queryKey: catalogKeys.dataset(id ?? ''),
    queryFn: () => catalogService.getDataset(id as string),
    enabled: Boolean(id),
    staleTime: FIVE_MIN,
  });
}

export function useLookup(lookupId: string | null | undefined) {
  return useQuery({
    queryKey: catalogKeys.lookup(lookupId ?? ''),
    queryFn: () => catalogService.getLookup(lookupId as string),
    enabled: Boolean(lookupId),
    staleTime: THIRTY_MIN,
  });
}

export function useDatasetQuery(id: string | null) {
  return useMutation({
    mutationFn: (vars: DatasetQueryVars) => catalogService.queryDataset(id as string, vars),
  });
}
