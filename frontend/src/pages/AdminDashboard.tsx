import { DashboardLayout } from "@/components/DashboardLayout";
import { StatCard } from "@/components/StatCard";
import { Users, UserCheck, Shield, TrendingUp, Settings, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const recentUsers = [
  { id: "1", name: "John Doe", email: "john@example.com", status: "active", joined: "2025-01-10" },
  { id: "2", name: "Jane Smith", email: "jane@example.com", status: "active", joined: "2025-01-12" },
  { id: "3", name: "Bob Wilson", email: "bob@example.com", status: "inactive", joined: "2025-01-14" },
  { id: "4", name: "Alice Brown", email: "alice@example.com", status: "active", joined: "2025-01-15" },
];

const AdminDashboard = () => {
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
          <Button className="bg-accent hover:bg-accent/90">
            <Settings className="h-4 w-4 mr-2" />
            System Settings
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value="12,847"
            change="+245 this week"
            changeType="positive"
            icon={Users}
          />
          <StatCard
            title="Active Users"
            value="9,423"
            change="73% active rate"
            changeType="positive"
            icon={UserCheck}
          />
          <StatCard
            title="Emails Quarantined"
            value="1.2M"
            change="+18% from last month"
            changeType="positive"
            icon={Shield}
          />
          <StatCard
            title="System Success Rate"
            value="97.8%"
            change="+1.2% improvement"
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
            <Button variant="outline" className="w-full">
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
            <Button variant="outline" className="w-full">
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
            <Button variant="outline" className="w-full">
              View Reports
            </Button>
          </Card>
        </div>

        {/* Recent Users Table */}
        <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold">Recent Users</h2>
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={user.status === "active" ? "default" : "secondary"}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{user.joined}</TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="ghost">
                        Manage
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
