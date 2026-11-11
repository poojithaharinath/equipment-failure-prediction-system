/**
 * useApi.js
 * Custom React hooks for data fetching with loading, error, and
 * refresh state management. Wraps the api service layer so pages
 * stay clean and consistent in their data-fetching patterns.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ---------------------------------------------------------------------------
// Core hook — single fetch on mount, optional auto-refresh
// ---------------------------------------------------------------------------

/**
 * Fetch data from an async function on mount and whenever `deps` change.
 *
 * @param {Function} fetchFn    Async function that returns data (e.g. () => api.getDashboardStats())
 * @param {Array}    deps       Dependency array — re-fetches when these change
 * @param {Object}   options
 * @param {number}   options.refreshInterval  Auto-refresh interval in ms (0 = disabled)
 * @param {any}      options.initialData      Initial value for `data` before first fetch
 *
 * @returns {{ data, loading, error, refresh }}
 */
export function useApi(fetchFn, deps = [], { refreshInterval = 0, initialData = null } = {}) {
  const [data, setData]       = useState(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const isMounted             = useRef(true);

  const run = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFn();
      if (isMounted.current) setData(result);
    } catch (err) {
      if (isMounted.current) {
        setError(err?.response?.data?.detail || err?.message || 'Unknown error');
      }
    } finally {
      if (isMounted.current) setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  // Run on mount + dep change
  useEffect(() => {
    isMounted.current = true;
    run();
    return () => { isMounted.current = false; };
  }, [run]);

  // Optional auto-refresh
  useEffect(() => {
    if (!refreshInterval) return;
    const id = setInterval(run, refreshInterval);
    return () => clearInterval(id);
  }, [run, refreshInterval]);

  return { data, loading, error, refresh: run };
}

// ---------------------------------------------------------------------------
// Paginated fetch hook
// ---------------------------------------------------------------------------

/**
 * Paginated data fetching hook.
 *
 * @param {Function} fetchFn   Async function accepting (page, pageSize, filters) → { items, total, page, page_size }
 * @param {Object}   filters   Filter parameters (triggers re-fetch on change)
 * @param {number}   pageSize  Items per page
 *
 * @returns {{ items, total, page, pageSize, loading, error, setPage, refresh }}
 */
export function usePaginatedApi(fetchFn, filters = {}, pageSize = 20) {
  const [items, setItems]     = useState([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const isMounted             = useRef(true);

  const filterKey = JSON.stringify(filters);

  const run = useCallback(async (pg = 1) => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFn({ page: pg, page_size: pageSize, ...filters });
      if (isMounted.current) {
        setItems(result.items ?? result);
        setTotal(result.total ?? (result.items ?? result).length);
        setPage(pg);
      }
    } catch (err) {
      if (isMounted.current)
        setError(err?.response?.data?.detail || err?.message || 'Unknown error');
    } finally {
      if (isMounted.current) setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey, pageSize]);

  useEffect(() => {
    isMounted.current = true;
    run(1);
    return () => { isMounted.current = false; };
  }, [run]);

  return {
    items,
    total,
    page,
    pageSize,
    loading,
    error,
    setPage: (pg) => run(pg),
    refresh: () => run(page),
  };
}

// ---------------------------------------------------------------------------
// Mutation hook — for POST / PATCH operations
// ---------------------------------------------------------------------------

/**
 * Mutation hook for create / update API calls.
 *
 * @param {Function} mutateFn  Async function that accepts payload and returns result
 * @param {Object}   options
 * @param {Function} options.onSuccess  Called with result after successful mutation
 * @param {Function} options.onError    Called with error after failed mutation
 *
 * @returns {{ mutate, loading, error, data }}
 */
export function useMutation(mutateFn, { onSuccess, onError } = {}) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const mutate = useCallback(async (payload) => {
    try {
      setLoading(true);
      setError(null);
      const result = await mutateFn(payload);
      setData(result);
      if (onSuccess) onSuccess(result);
      return result;
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Unknown error';
      setError(msg);
      if (onError) onError(msg, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [mutateFn, onSuccess, onError]);

  return { mutate, loading, error, data };
}

// ---------------------------------------------------------------------------
// Convenience wrappers for common API patterns
// ---------------------------------------------------------------------------

/**
 * Fetch and auto-refresh dashboard statistics every 60 seconds.
 * @param {Object} api  The imported api service object
 */
export function useDashboardStats(api) {
  return useApi(() => api.getDashboardStats(), [], { refreshInterval: 60_000 });
}

/**
 * Fetch the full prediction list for all machines.
 * @param {Object} api
 * @param {Object} params  Optional filter params (risk_category, sort_by)
 */
export function usePredictions(api, params = {}) {
  return useApi(() => api.getPredictions(params), [JSON.stringify(params)]);
}

/**
 * Fetch a single machine's latest prediction.
 * @param {Object} api
 * @param {string} machineId
 */
export function useMachinePrediction(api, machineId) {
  return useApi(
    () => machineId ? api.getMachinePrediction(machineId) : Promise.resolve(null),
    [machineId]
  );
}

/**
 * Fetch validation report and exceptions.
 * @param {Object} api
 */
export function useValidationReport(api) {
  return useApi(() => api.getValidationReport(), []);
}

/**
 * Fetch model evaluation metrics.
 * @param {Object} api
 */
export function useModelEvaluation(api) {
  return useApi(() => api.getModelEvaluation(), []);
}

