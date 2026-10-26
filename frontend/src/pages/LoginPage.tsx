import { type SubmitEvent, useState } from 'react'
import { tokenStore } from '@/api/client'
import { useLogin } from '@/api/queries'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Spinner } from '@/components/ui/spinner'

type Props = { onLogin: () => void; notice?: string }

export function LoginPage({ onLogin, notice }: Props) {
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    login.mutate(
      { email, password },
      {
        onSuccess: (token) => {
          tokenStore.set(token.access_token)
          onLogin()
        },
      },
    )
  }

  return (
    <main className="grid min-h-screen place-items-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-xl">Wind Forecast Monitor</CardTitle>
          <CardDescription>Day-ahead wind forecasts and how far to trust them</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={submit}>
            {notice && (
              <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{notice}</p>
            )}
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {login.error && <p className="text-sm text-destructive">{login.error.message}</p>}
            <Button type="submit" size="lg" disabled={login.isPending}>
              {login.isPending && <Spinner />}
              {login.isPending ? 'Signing in…' : 'Sign in'}
            </Button>
            <p className="text-sm text-muted-foreground">
              Demo account: <code>trader@example.com</code> / <code>windpower2026</code>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
