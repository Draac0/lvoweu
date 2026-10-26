import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Props<T> = {
  query: UseQueryResult<T>
  placeholder: ReactNode
  children: (data: T) => ReactNode
}

/** A query's error, its placeholder while loading, or its data (dimmed while new data loads). */
export function QueryContent<T>({ query, placeholder, children }: Props<T>) {
  if (query.isError) return <p className="text-destructive">{query.error.message}</p>
  if (query.data === undefined) return placeholder

  return (
    <div className={cn('transition-opacity', query.isPlaceholderData && 'opacity-50')}>
      {children(query.data)}
    </div>
  )
}
