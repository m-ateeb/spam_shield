import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { supabase } from '@/lib/supabaseClient'
import { syncTokenToExtension } from '@/lib/extensionAuth'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { FcGoogle } from 'react-icons/fc'
import { FaMicrosoft } from 'react-icons/fa'

export const Signup = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  // Email/password signup
  const handleSignup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { role: 'user' } },
    })
    setLoading(false)

    if (error) {
      setMessage(error.message)
      return
    }

    if (data.session) {
      // Sync auth to extension
      await syncTokenToExtension(data.session.access_token, data.session.user.email || '')
      navigate('/dashboard')
      return
    }

    setMessage('Check your email for confirmation!')
  }

  // OAuth signup/login
  const handleOAuth = async (provider: 'google' | 'azure') => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: window.location.origin + '/dashboard' },
    })
    setLoading(false)
    if (error) setMessage(error.message)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-md p-8 rounded-2xl shadow-xl space-y-6 bg-white dark:bg-gray-800">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-semibold">Create your account</CardTitle>
          <CardDescription>Start protecting your inbox in minutes.</CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {message && (
              <p className="text-sm text-red-500 text-center" role="status">
                {message}
              </p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          <Separator className="my-4" />

          <div className="flex flex-col gap-3">
            <Button
              variant="outline"
              className="flex items-center justify-center gap-2"
              onClick={() => handleOAuth('google')}
            >
              <FcGoogle size={20} /> Sign up with Google
            </Button>
            <Button
              variant="outline"
              className="flex items-center justify-center gap-2"
              onClick={() => handleOAuth('azure')}
            >
              <FaMicrosoft size={20} /> Sign up with Microsoft
            </Button>
          </div>

          <p className="mt-4 text-sm text-center text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

