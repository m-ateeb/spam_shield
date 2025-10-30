import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { supabase } from "@/lib/supabaseClient"
import { useAuth } from "@/context/AuthContext"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { FcGoogle } from "react-icons/fc"
import { FaMicrosoft } from "react-icons/fa"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const navigate = useNavigate()
  const { signInWithOAuth } = useAuth()

  // Email/password login
  const handleEmailLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")

    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)

    if (error) {
      setMessage(error.message)
      return
    }

    if (data.session) {
      navigate("/dashboard")
    }
  }

  // OAuth login
  const handleOAuthLogin = async (provider: "google" | "azure") => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: window.location.origin + "/dashboard" },
    })
    setLoading(false)
    if (error) setMessage(error.message)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-md p-8 rounded-2xl shadow-xl space-y-6 bg-white dark:bg-gray-800">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-semibold">Sign in to SpamShield</CardTitle>
          <CardDescription>Secure your inbox and stay protected</CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <form onSubmit={handleEmailLogin} className="space-y-4">
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
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          <Separator className="my-4" />

          <div className="flex flex-col gap-3">
            <Button
              variant="outline"
              className="flex items-center justify-center gap-2"
              onClick={() => handleOAuthLogin("google")}
            >
              <FcGoogle size={20} /> Sign in with Google
            </Button>
            <Button
              variant="outline"
              className="flex items-center justify-center gap-2"
              onClick={() => handleOAuthLogin("azure")}
            >
              <FaMicrosoft size={20} /> Sign in with Microsoft
            </Button>
          </div>

          <p className="mt-4 text-sm text-center text-gray-500">
            Don’t have an account?{" "}
            <Link to="/signup" className="text-blue-600 hover:underline">
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
