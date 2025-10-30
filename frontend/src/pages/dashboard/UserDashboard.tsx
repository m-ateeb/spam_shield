import { DashboardLayout } from "../../components/DashboardLayout";
import { StatCard } from "../../components/StatCard";
import { QuarantineTable } from "../../components/QuarantineTable";
import { ActivityChart } from "../../components/ActivityChart";
import { Mail, Shield, Inbox, TrendingUp } from "lucide-react";

const UserDashboard = () => {
  return (
    <DashboardLayout type="user">
      <div className="p-8 space-y-8">
        {/* Header */}
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">Welcome back, John</h1>
          <p className="text-muted-foreground">
            Here's your email protection summary for today
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Emails"
            value="1,247"
            change="+12% from last week"
            changeType="positive"
            icon={Mail}
          />
          <StatCard
            title="Spam Blocked"
            value="287"
            change="23% of total"
            changeType="neutral"
            icon={Shield}
          />
          <StatCard
            title="Clean Inbox"
            value="960"
            change="+8% from last week"
            changeType="positive"
            icon={Inbox}
          />
          <StatCard
            title="Success Rate"
            value="98.5%"
            change="+0.5% improvement"
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        {/* Chart */}
        <ActivityChart />

        {/* Quarantine Table */}
        <QuarantineTable />
      </div>
    </DashboardLayout>
  );
};

export default UserDashboard;
