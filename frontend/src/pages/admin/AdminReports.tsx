import { useEffect, useState } from "react";
import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { Users, Mail, Shield, TrendingUp } from "lucide-react";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import api from "../../lib/api";

interface ReportsData {
  overview: {
    total_users: number;
    active_users: number;
    total_emails: number;
    total_classified: number;
  };
  classification: {
    safe: number;
    suspicious: number;
    phishing: number;
    safe_percentage: number;
    spam_percentage: number;
  };
  recent_activity: {
    emails_last_7_days: number;
    emails_last_30_days: number;
    quarantined_last_7_days: number;
    quarantined_last_30_days: number;
  };
  top_users: Array<{
    id: number;
    username: string;
    email: string;
    email_count: number;
  }>;
  daily_stats: Array<{
    date: string;
    day_name: string;
    total_emails: number;
    safe: number;
    spam: number;
  }>;
}

const AdminReports = () => {
  const [data, setData] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
    const interval = setInterval(loadReports, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/admin/reports/");
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8 flex items-center justify-center min-h-[400px]">
          <div className="text-muted-foreground">Loading reports...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !data) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8">
          <div className="text-destructive">Error: {error || "No data available"}</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">Data Analytics & Reports</h1>
          <p className="text-muted-foreground">
            View detailed reports and analytics on system performance
          </p>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value={data.overview.total_users.toLocaleString()}
            change={`${data.overview.active_users} active`}
            changeType="positive"
            icon={Users}
          />
          <StatCard
            title="Total Emails"
            value={data.overview.total_emails.toLocaleString()}
            change={`${data.overview.total_classified} classified`}
            changeType="positive"
            icon={Mail}
          />
          <StatCard
            title="Safe Emails"
            value={data.classification.safe.toLocaleString()}
            change={`${data.classification.safe_percentage.toFixed(1)}%`}
            changeType="positive"
            icon={Shield}
          />
          <StatCard
            title="Spam Detected"
            value={(data.classification.suspicious + data.classification.phishing).toLocaleString()}
            change={`${data.classification.spam_percentage.toFixed(1)}%`}
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        {/* Daily Activity Chart */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Activity (Last 7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.daily_stats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day_name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="safe" fill="#22c55e" name="Safe" />
              <Bar dataKey="spam" fill="#ef4444" name="Spam" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Recent Activity & Top Users */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Emails (7 days):</span>
                <span className="font-medium">{data.recent_activity.emails_last_7_days}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Emails (30 days):</span>
                <span className="font-medium">{data.recent_activity.emails_last_30_days}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Quarantined (7 days):</span>
                <span className="font-medium">{data.recent_activity.quarantined_last_7_days}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Quarantined (30 days):</span>
                <span className="font-medium">{data.recent_activity.quarantined_last_30_days}</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Top Users by Email Count</h2>
            <div className="space-y-3">
              {data.top_users.slice(0, 5).map((user, index) => (
                <div key={user.id} className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{user.username || user.email}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                  <Badge variant="outline">{user.email_count} emails</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminReports;
