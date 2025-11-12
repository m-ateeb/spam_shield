import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, Shield, User, LogOut, Home, Mail, Settings, ChartBar } from "lucide-react";
import { cn } from "../lib/utils";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";

interface DashboardLayoutProps {
  children: ReactNode;
  type: "user" | "admin";
}

export const DashboardLayout = ({ children, type }: DashboardLayoutProps) => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const response = await api.get("/api/auth/admin/check/");
        // Explicitly check for true value, not just truthy
        const adminStatus = response.data?.is_admin === true;
        setIsAdmin(adminStatus);
      } catch (err) {
        // On error, definitely not admin
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    // Only check if user is authenticated
    if (user) {
      checkAdmin();
    } else {
      setLoading(false);
      setIsAdmin(false);
    }
  }, [user]);

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <Shield className="h-8 w-8 text-accent" />
            <span className="text-xl font-semibold">InboxGuardian</span>
          </div>
          
          <nav className="space-y-1">
            {/* User Dashboard - Always visible */}
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
            >
              <ChartBar className="h-5 w-5" />
              <span>Dashboard</span>
            </NavLink>
            
            {/* Admin Dashboard - Only visible to admins */}
            {!loading && isAdmin && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )
                }
              >
                <LayoutDashboard className="h-5 w-5" />
                <span>Admin Dashboard</span>
              </NavLink>
            )}
            <NavLink
              to="/quarantine"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
            >
              <Mail className="h-5 w-5" />
              <span>Quarantine</span>
            </NavLink>
            
            {/* Settings */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
            >
              <Settings className="h-5 w-5" />
              <span>Settings</span>
            </NavLink>
            
            <div className="my-4 border-t border-border"></div>
            
            {/* Home */}
            <NavLink
              to="/"
              className="flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <Home className="h-5 w-5" />
              <span>Home</span>
            </NavLink>
            
            {/* Logout */}
            <NavLink
              to="/logout"
              className="flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <LogOut className="h-5 w-5" />
              <span>Logout</span>
            </NavLink>
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};
