export interface ParamDef {
  name: string;
  type: string;
  required: boolean;
  label: string;
  format?: string;
  enum?: string[];
  description?: string;
  lookup_id?: string;
}

export interface CatalogColumn {
  field: string;
  type?: string;
  label?: string;
  format?: string;
}

export interface DatasetSummary {
  id: string;
  name: string;
  description?: string;
  category: string;
  category_label: string;
  param_count: number;
  is_date_partitioned: boolean;
  paginated: boolean;
  featured: boolean;
}

export interface DatasetDetail extends DatasetSummary {
  path: string;
  method: string;
  params: ParamDef[];
  columns: CatalogColumn[];
}

export interface CategoryInfo {
  id: string;
  label: string;
  dataset_count: number;
}

export interface CatalogCategories {
  featured: { id: string; name: string; category_label: string }[];
  categories: CategoryInfo[];
}

export interface QueryColumn {
  field: string;
  headerName: string;
}

export interface QueryResult {
  columns: QueryColumn[];
  data: Record<string, unknown>[];
  meta: { total: number; truncated: boolean; intervals: number };
}

export interface LookupOption {
  label: string;
  value: string | number;
}

export interface DatasetQueryVars {
  params: Record<string, unknown>;
  page?: { number: number; size: number };
}
