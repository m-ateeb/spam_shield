import { useEffect, useState } from "react";
import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { Users, UserCheck, Shield, TrendingUp, Settings, Database } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Badge } from "../../components/ui/badge";
import api from "../../lib/api";
import { useNavigate } from "react-router-dom";

interface AdminDashboardData {
  total_users: number;
  total_users_change: string;
  active_users: number;
  active_users_pct: string;
  emails_quarantined: number;
  emails_quarantined_change: string;
  system_success_rate: string;
  system_success_rate_change: string;
}

const AdminDashboard = () => {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await api.get("/api/dashboard/admin/summary/");
        setData(response.data);
        setError(null);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setError("Admin access required");
          navigate("/dashboard");
        } else {
          setError(err.response?.data?.error || "Failed to load admin dashboard");
        }
        console.error("Admin dashboard error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [navigate]);

  if (loading) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8 flex items-center justify-center min-h-[400px]">
          <div className="text-muted-foreground">Loading admin dashboard...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8">
          <div className="text-destructive">Error: {error}</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
            <p className="text-muted-foreground">
              Manage your antispam system and monitor performance
            </p>
          </div>
          <Button 
            className="bg-accent hover:bg-accent/90"
            onClick={() => navigate('/admin/settings')}
          >
            <Settings className="h-4 w-4 mr-2" />
            System Settings
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value={data?.total_users?.toLocaleString() || "0"}
            change={data?.total_users_change || "No data"}
            changeType="positive"
            icon={Users}
          />
          <StatCard
            title="Active Users"
            value={data?.active_users?.toLocaleString() || "0"}
            change={data?.active_users_pct || "0% active rate"}
            changeType="positive"
            icon={UserCheck}
          />
          <StatCard
            title="Emails Quarantined"
            value={data?.emails_quarantined?.toLocaleString() || "0"}
            change={data?.emails_quarantined_change || "No data"}
            changeType="positive"
            icon={Shield}
          />
          <StatCard
            title="System Success Rate"
            value={data?.system_success_rate || "0%"}
            change={data?.system_success_rate_change || "No change"}
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        {/* Management Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-lg transition-all duration-200 animate-slide-up border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-accent/10 rounded-lg">
                <Users className="h-6 w-6 text-accent" />
              </div>
              <h3 className="font-semibold text-lg">User Management</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Manage user accounts, permissions, and access control
            </p>
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => navigate('/admin/users')}
            >
              Manage Users
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all duration-200 animate-slide-up border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-success/10 rounded-lg">
                <Shield className="h-6 w-6 text-success" />
              </div>
              <h3 className="font-semibold text-lg">Spam Rules</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Configure spam detection rules and threat thresholds
            </p>
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => navigate('/admin/rules')}
            >
              Configure Rules
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all duration-200 animate-slide-up border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-destructive/10 rounded-lg">
                <Database className="h-6 w-6 text-destructive" />
              </div>
              <h3 className="font-semibold text-lg">Data Analytics</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              View detailed reports and analytics on system performance
            </p>
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => navigate('/admin/reports')}
            >
              View Reports
            </Button>
          </Card>
        </div>

        {/* Recent Users Table - Placeholder for future implementation */}
        <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold">Recent Users</h2>
          </div>
          <div className="p-8 text-center text-muted-foreground">
            User management feature coming soon
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
