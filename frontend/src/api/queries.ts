import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import { api, unwrap } from '@/api/client'

export function useDecisionForecasts(cutoff: string) {
  return useQuery({
    queryKey: ['decision-forecasts', cutoff],
    queryFn: () =>
      unwrap(api.GET('/api/v1/decision-forecasts', { params: { query: { cutoff } } })),
    // While a new cutoff loads, keep showing the previous numbers instead of a blank screen.
    placeholderData: keepPreviousData,
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      unwrap(api.POST('/api/v1/auth/login', { body: credentials })),
  })
}
