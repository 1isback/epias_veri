export const mockKpiData = {
  systemDemand: { value: 38247, unit: 'MW', trend: 1.2, isPositive: true },
  windOutput: { value: 8412, unit: 'MW', trend: 14.3, isPositive: true },
  solarOutput: { value: 2118, unit: 'MW', trend: 5.8, isPositive: true },
  gasGeneration: { value: 14220, unit: 'MW', trend: -8.2, isPositive: false },
  gridFrequency: { value: 49.98, unit: 'Hz', trend: -0.02, isPositive: false },
  spotPrice: { value: 84.32, unit: '£/MWh', trend: 2.6, isPositive: true },
};

export const mockMarketTicker = [
  { symbol: 'PWR-FR', price: 79.67, change: 0.52, changePercent: 0.66, isPositive: true },
  { symbol: 'GAS-NBP', price: 102.45, change: 3.39, changePercent: 3.42, isPositive: true },
  { symbol: 'GAS-TTF', price: 38.74, change: -0.88, changePercent: -2.22, isPositive: false },
  { symbol: 'EUA-DEC', price: 64.62, change: 1.06, changePercent: 1.66, isPositive: true },
  { symbol: 'BRENT', price: 82.46, change: -0.31, changePercent: -0.37, isPositive: false },
  { symbol: 'API2-Q1', price: 114.77, change: 2.72, changePercent: 2.43, isPositive: true },
];

export const mockChartData = Array.from({ length: 24 }).map((_, i) => ({
  time: `${i.toString().padStart(2, '0')}:00`,
  demand: 30000 + Math.random() * 10000,
  wind: 5000 + Math.random() * 5000,
  solar: i > 6 && i < 18 ? Math.random() * 8000 : 0,
  gas: 10000 + Math.random() * 5000,
}));

export const mockAlerts = [
  { id: '1', type: 'danger', title: 'Undervoltage', subtitle: 'ALT-0847 • Zone 7 • Bus 147', time: '02:14 ago', value: '-4.2' },
  { id: '2', type: 'warning', title: 'Frequency Deviation', subtitle: 'ALT-0846 • Zone 3 • AGC System', time: '08:31 ago', value: '-0.05 Hz' },
  { id: '3', type: 'warning', title: 'Line Thermal Limit', subtitle: 'ALT-0844 • Zone 12 • 400kV Line 12A', time: '15:02 ago', value: '94.2%' },
  { id: '4', type: 'danger', title: 'SCADA Comms Loss', subtitle: 'ALT-0841 • Zone 1 • RTU-NW-01', time: '21:45 ago', value: 'N/A' },
  { id: '5', type: 'primary', title: 'Reactive Power', subtitle: 'ALT-0839 • Zone 5 • Gen Unit 5B', time: '34:18 ago', value: '+12 MVAR' },
];

export const mockInterconnectors = [
  { id: 'IFA', name: 'IFA (FR→GB)', value: 1800, max: 2000, isPositive: true },
  { id: 'NEMO', name: 'NEMO (BE→GB)', value: 720, max: 1000, isPositive: true },
  { id: 'NSL', name: 'NSL (NO→GB)', value: 1400, max: 1400, isPositive: true },
  { id: 'BritNed', name: 'BritNed (NL)', value: -400, max: 1000, isPositive: false },
  { id: 'ElecLink', name: 'ElecLink (FR)', value: 480, max: 1000, isPositive: true },
];
