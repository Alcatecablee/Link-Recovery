import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const apiClient = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

// API functions
export const auth = {
  getStatus: () => apiClient.get('/auth/status'),
  demoLogin: () => apiClient.post('/auth/demo-login'),
  logout: () => apiClient.post('/auth/logout')
};

export const sites = {
  list: () => apiClient.get('/sites'),
  create: (siteUrl) => apiClient.post('/sites', { site_url: siteUrl }),
  scan: (siteId) => apiClient.post(`/sites/${siteId}/scan`)
};

export const errors = {
  list: (params) => apiClient.get('/errors', { params }),
  getDetails: (errorId) => apiClient.get(`/errors/${errorId}`),
  generateRecommendations: (errorId) => apiClient.post(`/errors/${errorId}/generate-recommendations`),
  updateStatus: (errorId, status) => apiClient.patch(`/errors/${errorId}`, { status })
};

export const dashboard = {
  getStats: () => apiClient.get('/dashboard/stats')
};

export default apiClient;