import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { Users, UserCheck, Shield, TrendingUp, Settings, Database } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useNavigate } from "react-router-dom";
import { useDashboard } from "../../hooks/useDashboard";
import { DashboardLoading } from "../../components/dashboard/DashboardLoading";
import { DashboardError } from "../../components/dashboard/DashboardError";
import { DashboardHeader } from "../../components/dashboard/DashboardHeader";
import { ManagementCard } from "../../components/dashboard/ManagementCard";

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
  const navigate = useNavigate();
  const { data, loading, error } = useDashboard("/api/dashboard/admin/summary/");

  if (loading) {
    return <DashboardLoading type="admin" message="Loading admin dashboard..." />;
  }

  if (error) {
    if (error === "Admin access required") {
      navigate("/dashboard");
      return null;
    }
    return <DashboardError type="admin" error={error} />;
  }

  const dashboardData = data as AdminDashboardData;

  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        <DashboardHeader
          title="Admin Dashboard"
          subtitle="Manage your antispam system and monitor performance"
          action={
            <Button
              className="bg-accent hover:bg-accent/90"
              onClick={() => navigate("/admin/settings")}
            >
              <Settings className="h-4 w-4 mr-2" />
              System Settings
            </Button>
          }
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value={dashboardData?.total_users?.toLocaleString() || "0"}
            change={dashboardData?.total_users_change || "No data"}
            changeType="positive"
            icon={Users}
          />
          <StatCard
            title="Active Users"
            value={dashboardData?.active_users?.toLocaleString() || "0"}
            change={dashboardData?.active_users_pct || "0% active rate"}
            changeType="positive"
            icon={UserCheck}
          />
          <StatCard
            title="Emails Quarantined"
            value={dashboardData?.emails_quarantined?.toLocaleString() || "0"}
            change={dashboardData?.emails_quarantined_change || "No data"}
            changeType="positive"
            icon={Shield}
          />
          <StatCard
            title="System Success Rate"
            value={dashboardData?.system_success_rate || "0%"}
            change={dashboardData?.system_success_rate_change || "No change"}
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ManagementCard
            icon={Users}
            title="User Management"
            description="Manage user accounts, permissions, and access control"
            buttonText="Manage Users"
            onClick={() => navigate("/admin/users")}
          />
          <ManagementCard
            icon={Shield}
            title="Spam Rules"
            description="Configure spam detection rules and threat thresholds"
            buttonText="Configure Rules"
            onClick={() => navigate("/admin/rules")}
            iconBg="bg-success/10"
            iconColor="text-success"
          />
          <ManagementCard
            icon={Database}
            title="Data Analytics"
            description="View detailed reports and analytics on system performance"
            buttonText="View Reports"
            onClick={() => navigate("/admin/reports")}
            iconBg="bg-destructive/10"
            iconColor="text-destructive"
          />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
