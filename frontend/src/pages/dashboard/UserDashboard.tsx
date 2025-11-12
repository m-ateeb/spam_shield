import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { QuarantineTable } from "../../components/QuarantineTable";
import { ActivityChart } from "../../components/ActivityChart";
import { Mail, Shield, Inbox, TrendingUp } from "lucide-react";
import { useDashboard } from "../../hooks/useDashboard";
import { DashboardLoading } from "../../components/dashboard/DashboardLoading";
import { DashboardError } from "../../components/dashboard/DashboardError";
import { DashboardHeader } from "../../components/dashboard/DashboardHeader";

interface DashboardData {
  user_email: string;
  user_name: string;
  total_emails: number;
  total_emails_change: string;
  spam_blocked: number;
  spam_blocked_pct: string;
  clean_inbox: number;
  clean_inbox_change: string;
  success_rate: string;
  success_rate_change: string;
  quarantined_emails: number;
  suspicious_emails: number;
}

const UserDashboard = () => {
  const { data, loading, error } = useDashboard("/api/dashboard/summary/");

  if (loading) {
    return <DashboardLoading type="user" />;
  }

  if (error) {
    return <DashboardError type="user" error={error} />;
  }

  const dashboardData = data as DashboardData;

  return (
    <DashboardLayout type="user">
      <div className="p-8 space-y-8">
        <DashboardHeader
          title={`Welcome back, ${dashboardData?.user_name || dashboardData?.user_email || "User"}`}
          subtitle="Here's your email protection summary"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Emails"
            value={dashboardData?.total_emails?.toLocaleString() || "0"}
            change={dashboardData?.total_emails_change || "No data"}
            changeType="positive"
            icon={Mail}
          />
          <StatCard
            title="Spam Blocked"
            value={dashboardData?.spam_blocked?.toLocaleString() || "0"}
            change={dashboardData?.spam_blocked_pct || "0% of total"}
            changeType="neutral"
            icon={Shield}
          />
          <StatCard
            title="Clean Inbox"
            value={dashboardData?.clean_inbox?.toLocaleString() || "0"}
            change={dashboardData?.clean_inbox_change || "No data"}
            changeType="positive"
            icon={Inbox}
          />
          <StatCard
            title="Success Rate"
            value={dashboardData?.success_rate || "0%"}
            change={dashboardData?.success_rate_change || "No change"}
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        <ActivityChart />
        <QuarantineTable limit={5} />
      </div>
    </DashboardLayout>
  );
};

export default UserDashboard;
