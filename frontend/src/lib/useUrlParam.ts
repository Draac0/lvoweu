import { useState } from 'react'

/** A string kept in the page URL (?name=value), so a view can be bookmarked or shared. */
export function useUrlParam(name: string, fallback: string) {
  const [value, setValue] = useState(
    () => new URLSearchParams(window.location.search).get(name) ?? fallback,
  )

  function update(next: string) {
    const params = new URLSearchParams(window.location.search)
    params.set(name, next)
    window.history.replaceState(null, '', `?${params}`)
    setValue(next)
  }

  return [value, update] as const
}
