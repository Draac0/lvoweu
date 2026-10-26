import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import { api, unwrap } from '@/api/client'

// Every hook keeps showing the previous result while new parameters load
// (placeholderData), so the UI dims instead of flashing empty.

export function useSummary(cutoff: string) {
  return useQuery({
    queryKey: ['summary', cutoff],
    queryFn: () => unwrap(api.GET('/api/v1/accuracy/summary', { params: { query: { cutoff } } })),
    placeholderData: keepPreviousData,
  })
}

export function useDays(cutoff: string) {
  return useQuery({
    queryKey: ['days', cutoff],
    queryFn: () => unwrap(api.GET('/api/v1/days', { params: { query: { cutoff } } })),
    placeholderData: keepPreviousData,
  })
}

export function useDay(day: string | undefined, cutoff: string) {
  return useQuery({
    queryKey: ['day', day, cutoff],
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/days/{day}', { params: { path: { day: day! }, query: { cutoff } } }),
      ),
    enabled: day !== undefined,
    placeholderData: keepPreviousData,
  })
}

/** Every forecast published for one target hour. */
export function useForecastHistory(startTime: string | undefined) {
  return useQuery({
    queryKey: ['forecast-history', startTime],
    queryFn: () =>
      unwrap(api.GET('/api/v1/forecasts', { params: { query: { start_time: startTime! } } })),
    enabled: startTime !== undefined,
    placeholderData: keepPreviousData,
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      unwrap(api.POST('/api/v1/auth/login', { body: credentials })),
  })
}
