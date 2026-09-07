export const mockCompanyData = {
  id: 'c-demo-1',
  name: 'Energy Company A',
  type: 'Generation & Supply',
  founded: '1998',
  headquarters: 'London, UK',
  totalCapacity: '4,520 MW',
  activeAssets: 12,
  description: 'Energy Company A is a leading provider of sustainable and reliable energy solutions, focusing on renewable generation and efficient grid support operations.',
};

export const mockCompanyAssets = [
  { id: 'a1', name: 'Demo Wind Farm North', type: 'Wind', capacity: 850, currentOutput: 720, status: 'ONLINE', capacityFactor: 84.7 },
  { id: 'a2', name: 'Demo Gas Plant 1', type: 'Gas', capacity: 1200, currentOutput: 450, status: 'ONLINE', capacityFactor: 37.5 },
  { id: 'a3', name: 'Demo Solar Park', type: 'Solar', capacity: 300, currentOutput: 0, status: 'OFFLINE', capacityFactor: 0 },
  { id: 'a4', name: 'Demo Nuclear Unit', type: 'Nuclear', capacity: 2170, currentOutput: 2170, status: 'ONLINE', capacityFactor: 100 },
];
