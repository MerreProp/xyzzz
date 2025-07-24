import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api', // This will use the proxy we set up
  timeout: 30000,
});

// API endpoints
export const propertyApi = {
  // Start property analysis
  analyzeProperty: async (url) => {
    const response = await api.post('/analyze', { url });
    return response.data;
  },

  // Get analysis status
  getAnalysisStatus: async (taskId) => {
    const response = await api.get(`/analysis/${taskId}`);
    return response.data;
  },

  // Get all analyzed properties
  getAllProperties: async () => {
    const response = await api.get('/properties');
    return response.data;
  },

  // Get specific property details
  getPropertyDetails: async (propertyId) => {
    const response = await api.get(`/properties/${propertyId}`);
    return response.data;
  },

  // Export property to Excel
  exportProperty: async (propertyId) => {
    const response = await api.get(`/export/${propertyId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Delete analysis
  deleteAnalysis: async (taskId) => {
    const response = await api.delete(`/analysis/${taskId}`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

// Helper function to download file from blob
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

// Helper function to validate SpareRoom URL
export const isValidSpareRoomUrl = (url) => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.includes('spareroom.co.uk');
  } catch {
    return false;
  }
};

export const analyzeProperty = async ({ url, force_separate = false }) => {
  const response = await api.post('/analyze', { 
    url, 
    force_separate 
  });
  return response.data;
};

export default api;