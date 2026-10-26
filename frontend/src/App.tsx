import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { setUnauthorizedHandler, tokenStore } from '@/api/client'
import { Dashboard } from '@/pages/Dashboard'
import { LoginPage } from '@/pages/LoginPage'

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

  return loggedIn ? <Dashboard onLogout={logout} /> : <LoginPage onLogin={login} notice={notice} />
}
