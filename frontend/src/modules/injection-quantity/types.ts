export interface InjectionQuantityPowerplant {
  epias_powerplant_id: number;
  name: string | null;
  short_name: string | null;
  eic: string | null;
}

export interface InjectionQuantityRecord {
  date: string;
  hour: number;
  total: number | null;
}

export interface InjectionQuantityListResponse {
  items: InjectionQuantityRecord[];
  total: number;
}

export interface InjectionQuantitySyncRequest {
  powerplant_id: number;
  start_date: string;
  end_date: string;
  force_refresh: boolean;
}

export interface InjectionQuantitySyncResponse {
  powerplant_id: number;
  requested_start_date: string;
  requested_end_date: string;
  chunk_count: number;
  fetched_record_count: number;
  inserted_record_count: number;
  updated_record_count: number;
  duplicate_record_count: number;
  status: string;
}

export interface InjectionQuantityFilters {
  powerplantId: number | null;
  startDate: string;
  endDate: string;
}

export interface InjectionQuantityService {
  syncPowerplants(): Promise<{ synced_count: number }>;
  listPowerplants(search?: string): Promise<InjectionQuantityPowerplant[]>;
  sync(request: InjectionQuantitySyncRequest): Promise<InjectionQuantitySyncResponse>;
  list(filters: Required<InjectionQuantityFilters>): Promise<InjectionQuantityListResponse>;
}
