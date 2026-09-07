export const env = {
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  DASHBOARD_REFRESH_INTERVAL: Number(process.env.NEXT_PUBLIC_DASHBOARD_REFRESH_INTERVAL) || 60000,
};
