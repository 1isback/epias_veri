export const mockExplorerData = Array.from({ length: 50 }).map((_, i) => ({
  id: `row-${i}`,
  date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
  dataset: i % 2 === 0 ? 'Day Ahead Market' : 'Intraday Market',
  price: (Math.random() * 100).toFixed(2),
  volume: Math.floor(Math.random() * 10000),
  status: Math.random() > 0.1 ? 'Matched' : 'Pending',
}));
