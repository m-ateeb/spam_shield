import { useEffect, useState } from "react";
import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { QuarantineTable } from "../../components/QuarantineTable";
import { ActivityChart } from "../../components/ActivityChart";
import { Mail, Shield, Inbox, TrendingUp } from "lucide-react";
import api from "../../lib/api";

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
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await api.get("/api/dashboard/summary/");
        setData(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.error || "Failed to load dashboard data");
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout type="user">
        <div className="p-8 flex items-center justify-center min-h-[400px]">
          <div className="text-muted-foreground">Loading dashboard...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout type="user">
        <div className="p-8">
          <div className="text-destructive">Error: {error}</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout type="user">
      <div className="p-8 space-y-8">
        {/* Header */}
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">
            Welcome back, {data?.user_name || data?.user_email || "User"}
          </h1>
          <p className="text-muted-foreground">
            Here's your email protection summary
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Emails"
            value={data?.total_emails?.toLocaleString() || "0"}
            change={data?.total_emails_change || "No data"}
            changeType="positive"
            icon={Mail}
          />
          <StatCard
            title="Spam Blocked"
            value={data?.spam_blocked?.toLocaleString() || "0"}
            change={data?.spam_blocked_pct || "0% of total"}
            changeType="neutral"
            icon={Shield}
          />
          <StatCard
            title="Clean Inbox"
            value={data?.clean_inbox?.toLocaleString() || "0"}
            change={data?.clean_inbox_change || "No data"}
            changeType="positive"
            icon={Inbox}
          />
          <StatCard
            title="Success Rate"
            value={data?.success_rate || "0%"}
            change={data?.success_rate_change || "No change"}
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        {/* Chart */}
        <ActivityChart />

        {/* Quarantine Table */}
        <QuarantineTable limit={5} />
      </div>
    </DashboardLayout>
  );
};

export default UserDashboard;
