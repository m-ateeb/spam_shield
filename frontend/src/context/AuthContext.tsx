import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import type { Session, User, AuthChangeEvent } from "@supabase/supabase-js";
import { syncTokenToExtension, clearExtensionAuth } from "@/lib/extensionAuth";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signInWithOAuth: (provider: "google" | "azure") => Promise<void>;
  signOut: () => Promise<void>;
  getJWT: () => string | null;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signInWithOAuth: async () => {},
  signOut: async () => {},
  getJWT: () => null,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    // Listen to auth changes
    const { data: listener } = supabase.auth.onAuthStateChange(
      async (event: AuthChangeEvent, session: Session | null) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
        
        // Sync to extension on sign in
        if (event === 'SIGNED_IN' && session) {
          await syncTokenToExtension(session.access_token, session.user.email || '');
        }
        
        // Clear extension on sign out
        if (event === 'SIGNED_OUT') {
          await clearExtensionAuth();
        }
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  const signInWithOAuth = async (provider: "google" | "azure") => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
    if (error) console.error("OAuth error:", error.message);
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
  };

  // Function to get JWT for your backend API calls
  const getJWT = () => session?.access_token ?? null;

  return (
    <AuthContext.Provider
      value={{ user, session, loading, signInWithOAuth, signOut, getJWT }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
