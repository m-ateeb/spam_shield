import { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";
import { syncTokenToExtension, clearExtensionAuth } from "@/lib/extensionAuth";

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithOAuth: (provider: "google" | "microsoft") => Promise<void>;
  signOut: () => Promise<void>;
  getToken: () => string | null;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signInWithOAuth: async () => {},
  signOut: async () => {},
  getToken: () => null,
  refreshUser: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem("auth_token");
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      const response = await api.get("/api/auth/user/");
      setUser(response.data);
      
      // Sync token to extension
      await syncTokenToExtension(token, response.data.email);
    } catch (error) {
      console.error("Failed to refresh user:", error);
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem("auth_token");
    if (token) {
      refreshUser();
    } else {
      setLoading(false);
    }
  }, []);

  const signInWithOAuth = async (provider: "google" | "microsoft") => {
    // Redirect to Django allauth OAuth endpoint with frontend redirect
    const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const frontendUrl = window.location.origin;
    const providerPath = provider === "google" ? "google" : "microsoft";
    window.location.href = `${apiUrl}/api/auth/${providerPath}/?redirect=${encodeURIComponent(frontendUrl)}`;
  };

  const signOut = async () => {
    try {
      // Call Django logout endpoint
      await api.post("/accounts/logout/");
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      setUser(null);
      await clearExtensionAuth();
    }
  };

  const getToken = () => {
    return localStorage.getItem("auth_token");
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, signInWithOAuth, signOut, getToken, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
