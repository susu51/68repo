/**
 * Custom hook for fetching business dashboard summary
 * Provides real-time metrics with loading/error states
 */

import { useState, useEffect, useCallback, useRef } from 'react';
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
  const [fetchCount, setFetchCount] = useState(0);
  
  // Use refs to avoid recreating fetchData on every render
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [onSuccess, onError]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('📊 Fetching dashboard summary...');
      const response = await getDashboardSummary(date, 'Europe/Istanbul');
      
      // Handle both response formats (response.data or direct response)
      const summaryData = response?.data || response;
      
      if (!summaryData) {
        throw new Error('No data received from server');
      }

      console.log('✅ Dashboard data loaded:', summaryData);
      setData(summaryData);
      setFetchCount(prev => prev + 1);
      
      if (onSuccessRef.current) {
        onSuccessRef.current(summaryData);
      }
    } catch (err) {
      console.error('❌ Dashboard summary fetch error:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load dashboard data';
      setError(errorMessage);
      
      if (onErrorRef.current) {
        onErrorRef.current(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [date]); // Only depend on date

  // Initial fetch - only once on mount
  useEffect(() => {
    let mounted = true;
    
    if (mounted) {
      fetchData();
    }
    
    return () => {
      mounted = false;
    };
  }, []); // Empty deps - fetch only once on mount

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
    refetch,
    fetchCount // For debugging
  };
};
