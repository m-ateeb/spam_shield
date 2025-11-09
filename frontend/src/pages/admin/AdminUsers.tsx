import { useEffect, useState } from "react";
import { DashboardLayout } from "../../components/DashboardLayout";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import api from "../../lib/api";
import { Shield, UserX, UserCheck, Crown } from "lucide-react";

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login: string | null;
  stats: {
    total_emails: number;
    safe_emails: number;
    malicious_emails: number;
    quarantined: number;
    connected_accounts: number;
  };
}

const AdminUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/admin/users/");
      setUsers(response.data.users || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const updateUser = async (userId: number, updates: any) => {
    try {
      await api.post("/api/admin/users/update/", {
        user_id: userId,
        ...updates,
      });
      loadUsers(); // Reload after update
    } catch (err: any) {
      alert(err.response?.data?.error || "Failed to update user");
    }
  };

  if (loading) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8 flex items-center justify-center min-h-[400px]">
          <div className="text-muted-foreground">Loading users...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">User Management</h1>
          <p className="text-muted-foreground">
            Manage user accounts, permissions, and access control
          </p>
        </div>

        {error && (
          <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
            {error}
          </div>
        )}

        <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold">All Users ({users.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Stats</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{user.username || user.email}</div>
                        <div className="text-sm text-muted-foreground">{user.email}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? "default" : "secondary"}>
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {user.is_superuser && (
                          <Badge variant="outline" className="gap-1">
                            <Crown className="h-3 w-3" />
                            Admin
                          </Badge>
                        )}
                        {user.is_staff && !user.is_superuser && (
                          <Badge variant="outline">Staff</Badge>
                        )}
                        {!user.is_staff && <Badge variant="outline">User</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div>📧 {user.stats.total_emails} emails</div>
                        <div>✅ {user.stats.safe_emails} safe</div>
                        <div>⚠️ {user.stats.malicious_emails} spam</div>
                        <div>🔗 {user.stats.connected_accounts} accounts</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-muted-foreground">
                        {new Date(user.date_joined).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateUser(user.id, { is_active: !user.is_active })}
                        >
                          {user.is_active ? (
                            <>
                              <UserX className="h-4 w-4 mr-1" />
                              Deactivate
                            </>
                          ) : (
                            <>
                              <UserCheck className="h-4 w-4 mr-1" />
                              Activate
                            </>
                          )}
                        </Button>
                        {!user.is_superuser && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => updateUser(user.id, { is_staff: !user.is_staff })}
                          >
                            <Shield className="h-4 w-4 mr-1" />
                            {user.is_staff ? "Remove Staff" : "Make Staff"}
                          </Button>
                        )}
                      </div>
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

export default AdminUsers;
