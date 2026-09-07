export interface CompanyAsset {
  id: string;
  name: string;
  type: 'Wind' | 'Solar' | 'Gas' | 'Nuclear' | 'Hydro';
  capacity: number;
  output: number;
  status: 'Online' | 'Offline' | 'Maintenance';
}

export interface CompanyDetails {
  id: string;
  name: string;
  totalCapacity: number;
  activeOutput: number;
  marketShare: number;
  employees: number;
  foundedYear: number;
}

export interface CompanyProductionData {
  time: string;
  wind: number;
  gas: number;
  nuclear: number;
}

export interface CompanyOverviewResponse {
  details: CompanyDetails;
  assets: CompanyAsset[];
  production: CompanyProductionData[];
}

export interface ICompanyService {
  getOverview(companyId: string): Promise<CompanyOverviewResponse>;
}
