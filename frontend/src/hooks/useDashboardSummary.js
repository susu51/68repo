/**
 * Custom hook for fetching business dashboard summary
 * Provides real-time metrics with loading/error states
 */

import { useState, useEffect, useCallback } from 'react';
import { getDashboardSummary } from '../api/businessDashboard';

/**
 * Hook to fetch and manage dashboard summary data
 * @param {string} date - Optional date filter (YYYY-MM-DD)
 * @param {Object} options - Configuration options
 * @returns {Object} { data, loading, error, refetch }
 */
export const useDashboardSummary = (date = null, options = {}) => {
  const {
    autoRefetch = false,
    refetchInterval = 30000, // 30 seconds
    onSuccess = null,
    onError = null
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getDashboardSummary(date, 'Europe/Istanbul');
      
      // Handle both response formats (response.data or direct response)
      const summaryData = response?.data || response;
      
      if (!summaryData) {
        throw new Error('No data received from server');
      }

      setData(summaryData);
      
      if (onSuccess) {
        onSuccess(summaryData);
      }
    } catch (err) {
      console.error('❌ Dashboard summary fetch error:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load dashboard data';
      setError(errorMessage);
      
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [date, onSuccess, onError]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refetch interval
  useEffect(() => {
    if (autoRefetch && refetchInterval > 0) {
      const intervalId = setInterval(() => {
        fetchData();
      }, refetchInterval);

      return () => clearInterval(intervalId);
    }
  }, [autoRefetch, refetchInterval, fetchData]);

  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch
  };
};
