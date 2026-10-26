import { useQueryClient } from '@tanstack/react-query'
import { lazy, Suspense, useEffect, useState } from 'react'
import { setUnauthorizedHandler, tokenStore } from '@/api/client'
import { Spinner } from '@/components/ui/spinner'
import { LoginPage } from '@/pages/LoginPage'

// Loaded only after login: keeps the charting library out of the first page's download.
const Dashboard = lazy(() => import('@/pages/Dashboard').then((m) => ({ default: m.Dashboard })))

export default function App() {
  const queryClient = useQueryClient()
  const [loggedIn, setLoggedIn] = useState(() => tokenStore.get() !== null)
  const [notice, setNotice] = useState<string>()

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setNotice('Your session expired. Please sign in again.')
      setLoggedIn(false)
    })
  }, [])

  function login() {
    setNotice(undefined)
    setLoggedIn(true)
  }

  function logout() {
    tokenStore.clear()
    queryClient.clear() // don't leave one user's data cached for the next
    setLoggedIn(false)
  }

  if (!loggedIn) return <LoginPage onLogin={login} notice={notice} />

  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center">
          <Spinner className="size-6 text-muted-foreground" />
        </div>
      }
    >
      <Dashboard onLogout={logout} />
    </Suspense>
  )
}
