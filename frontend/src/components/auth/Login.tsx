import { useState, useEffect } from "react"
import { useNavigate, Link, useSearchParams } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import api from "@/lib/api"
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
  const { signInWithOAuth, refreshUser } = useAuth()
  const [searchParams] = useSearchParams()

  // Handle OAuth callback - check if we have a token from Django allauth
  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");
    
    if (token) {
      localStorage.setItem("auth_token", token);
      refreshUser().then(() => {
        // Check for returnUrl in URL params or sessionStorage (for OAuth)
        const returnUrl = searchParams.get("returnUrl") || sessionStorage.getItem("oauth_return_url");
        if (returnUrl) {
          sessionStorage.removeItem("oauth_return_url"); // Clean up
          navigate(decodeURIComponent(returnUrl));
        } else {
          navigate("/dashboard");
        }
      });
    } else if (error) {
      // Handle OAuth errors
      let errorMessage = "Third-Party Login Failure";
      if (error === "oauth_failed") {
        errorMessage = "An error occurred while attempting to login via your third-party account. Please try again.";
      } else {
        errorMessage = `An error occurred while attempting to login via your third-party account: ${error}`;
      }
      setMessage(errorMessage);
      // Clear the error parameter from URL
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete("error");
      navigate(`/login?${newSearchParams.toString()}`, { replace: true });
    }
  }, [searchParams, navigate, refreshUser]);

  // Email/password login
  const handleEmailLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")

    try {
      const response = await api.post('/api/auth/login/', {
        email,
        password,
      })
      
      if (response.data.token) {
        localStorage.setItem("auth_token", response.data.token)
        await refreshUser()
        // Redirect to returnUrl if provided, otherwise dashboard
        const returnUrl = searchParams.get("returnUrl");
        navigate(returnUrl ? decodeURIComponent(returnUrl) : "/dashboard")
      }
    } catch (error: any) {
      setMessage(error.response?.data?.error || "Login failed. Please check your credentials.")
    } finally {
      setLoading(false)
    }
  }

  // OAuth login
  const handleOAuthLogin = async (provider: "google" | "microsoft") => {
    setLoading(true)
    // Preserve returnUrl in OAuth flow
    const returnUrl = searchParams.get("returnUrl");
    if (returnUrl) {
      // Store returnUrl in sessionStorage to retrieve after OAuth callback
      sessionStorage.setItem("oauth_return_url", returnUrl);
    }
    await signInWithOAuth(provider)
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-md p-8 rounded-2xl shadow-xl space-y-6 bg-white dark:bg-gray-800">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-3xl font-bold">Welcome to SpamShield</CardTitle>
          <CardDescription className="text-base">Sign in to protect your inbox from spam and phishing</CardDescription>
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
                disabled={loading}
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
                disabled={loading}
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

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <Separator />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-gray-800 px-2 text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <Button
              variant="outline"
              className="flex items-center justify-center gap-3 h-11"
              onClick={() => handleOAuthLogin("google")}
              disabled={loading}
            >
              <FcGoogle size={22} /> Sign in with Google
            </Button>
            <Button
              variant="outline"
              className="flex items-center justify-center gap-3 h-11"
              onClick={() => handleOAuthLogin("microsoft")}
              disabled={loading}
            >
              <FaMicrosoft size={22} className="text-blue-600" /> Sign in with Microsoft
            </Button>
          </div>

          <p className="mt-4 text-sm text-center text-gray-500">
            Don't have an account?{" "}
            <Link to="/signup" className="text-blue-600 hover:underline font-medium">
              Sign up here
            </Link>
            {" "}or use OAuth to create one automatically.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
