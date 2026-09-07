import { create } from 'zustand';

interface FilterState {
  dateRange: { start: string | null; end: string | null };
  selectedDatasets: string[];
  setDateRange: (start: string, end: string) => void;
  setSelectedDatasets: (datasets: string[]) => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  dateRange: { start: null, end: null },
  selectedDatasets: [],
  setDateRange: (start, end) => set({ dateRange: { start, end } }),
  setSelectedDatasets: (datasets) => set({ selectedDatasets: datasets }),
}));
