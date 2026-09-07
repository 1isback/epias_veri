import { apiClient } from '@/lib/api-client/apiClient';
import {
  CatalogCategories,
  DatasetDetail,
  DatasetQueryVars,
  DatasetSummary,
  LookupOption,
  QueryResult,
} from './types';

export interface DatasetListFilters {
  category?: string;
  q?: string;
  featured?: boolean;
}

export const catalogService = {
  getCategories: () => apiClient.get<unknown, CatalogCategories>('/catalog/categories'),

  listDatasets: (filters: DatasetListFilters) =>
    apiClient.get<unknown, DatasetSummary[]>('/catalog/datasets', { params: filters }),

  getDataset: (id: string) => apiClient.get<unknown, DatasetDetail>(`/catalog/datasets/${id}`),

  queryDataset: (id: string, body: DatasetQueryVars) =>
    apiClient.post<unknown, QueryResult>(`/catalog/datasets/${id}/query`, body),

  getLookup: (id: string) => apiClient.get<unknown, LookupOption[]>(`/catalog/lookups/${id}`),
};
