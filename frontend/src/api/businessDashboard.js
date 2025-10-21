/**
 * Business Dashboard API
 * Handles dashboard summary data fetching
 */

import { get } from './http';

/**
 * Fetch dashboard summary with real-time metrics
 * @param {string} date - Optional date in YYYY-MM-DD format
 * @param {string} tz - Timezone (default: Europe/Istanbul)
 * @returns {Promise} Dashboard summary data
 */
export const getDashboardSummary = async (date = null, tz = 'Europe/Istanbul') => {
  const params = { tz };
  if (date) {
    params.date = date;
  }
  
  const queryString = new URLSearchParams(params).toString();
  const response = await get(`/business/dashboard/summary?${queryString}`);
  
  return response;
};
