// useAnalysis.js - React Query hooks for HMO Analyser with Phase 1 functionality

import { useQuery } from '@tanstack/react-query';

// Phase 1: Availability data hooks
export const useAvailabilityData = (propertyId) => {
  return useQuery({
    queryKey: ['availability-summary', propertyId],
    queryFn: async () => {
      const response = await fetch(`/api/properties/${propertyId}/availability-summary`);
      if (!response.ok) {
        throw new Error('Failed to fetch availability data');
      }
      return response.json();
    },
    enabled: !!propertyId
  });
};

export const useRoomPeriods = (propertyId, roomId) => {
  return useQuery({
    queryKey: ['room-periods', propertyId, roomId],
    queryFn: async () => {
      const response = await fetch(`/api/properties/${propertyId}/rooms/${roomId}/periods`);
      if (!response.ok) {
        throw new Error('Failed to fetch room periods');
      }
      return response.json();
    },
    enabled: !!(propertyId && roomId)
  });
};

// Phase 1: Analytics hooks
export const useAvailabilityAnalytics = () => {
  return useQuery({
    queryKey: ['availability-analytics'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/availability');
      if (!response.ok) {
        throw new Error('Failed to fetch availability analytics');
      }
      return response.json();
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });
};

export const useRecentPeriods = (days = 7, limit = 10) => {
  return useQuery({
    queryKey: ['recent-periods', days, limit],
    queryFn: async () => {
      const response = await fetch(`/api/rooms/periods/recent?days=${days}&limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recent periods');
      }
      return response.json();
    }
  });
};

// Phase 1: Health check with availability stats
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health-check'],
    queryFn: async () => {
      const response = await fetch('/api/health');
      if (!response.ok) {
        throw new Error('Failed to fetch health data');
      }
      return response.json();
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });
};

// Utility hook for property changes
export const usePropertyChanges = (propertyId, limit = 50) => {
  return useQuery({
    queryKey: ['property-changes', propertyId, limit],
    queryFn: async () => {
      const response = await fetch(`/api/properties/${propertyId}/changes?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch property changes');
      }
      return response.json();
    },
    enabled: !!propertyId
  });
};

// Utility hook for recent changes across all properties
export const useRecentChanges = (days = 7, limit = 100) => {
  return useQuery({
    queryKey: ['recent-changes', days, limit],
    queryFn: async () => {
      const response = await fetch(`/api/changes/recent?days=${days}&limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recent changes');
      }
      return response.json();
    }
  });
};

// Phase 2

export const usePriceTrends = (propertyId, days = 90) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/properties/${propertyId}/price-trends?days=${days}`);
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch price trends:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (propertyId) fetchData();
  }, [propertyId, days]);
  
  return { data, isLoading };
};

export const usePropertyAnalytics = (propertyId) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/properties/${propertyId}/analytics`);
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (propertyId) fetchData();
  }, [propertyId]);
  
  return { data, isLoading };
};