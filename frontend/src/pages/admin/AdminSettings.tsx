import { DashboardLayout } from "../../components/DashboardLayout";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Save } from "lucide-react";

const AdminSettings = () => {
  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        <div className="flex items-center justify-between animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold mb-2">System Settings</h1>
            <p className="text-muted-foreground">
              Configure system-wide settings and preferences
            </p>
          </div>
          <Button>
            <Save className="h-4 w-4 mr-2" />
            Save Settings
          </Button>
        </div>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Email Processing</h2>
          <div className="space-y-4">
            <div>
              <Label>Max Emails Per User</Label>
              <Input type="number" defaultValue="10000" />
            </div>
            <div>
              <Label>Auto-Delete Quarantined After (days)</Label>
              <Input type="number" defaultValue="30" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Notification Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="h-4 w-4" />
              <Label>Email notifications for admin</Label>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="h-4 w-4" />
              <Label>Weekly summary reports</Label>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">System Maintenance</h2>
          <div className="space-y-4">
            <Button variant="outline">Clear Old Logs</Button>
            <Button variant="outline">Optimize Database</Button>
            <Button variant="outline">Backup System</Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AdminSettings;
