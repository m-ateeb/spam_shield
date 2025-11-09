import { useEffect, useState } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import api from "../lib/api";
import { Mail, Trash2, RefreshCw, X } from "lucide-react";

interface ConnectedAccount {
  id: number;
  email_address: string;
  provider: string;
  inbox_sync_status: string;
  token_expiry: string | null;
}

const Settings = () => {
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAccounts();
    
    // Check for OAuth success/error in URL
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccess = urlParams.get('oauth_success');
    const oauthError = urlParams.get('oauth_error');
    
    if (oauthSuccess) {
      // Reload accounts after successful OAuth
      setTimeout(() => {
        loadAccounts();
        // Clean URL
        window.history.replaceState({}, '', window.location.pathname);
      }, 1000);
    } else if (oauthError) {
      setError(`OAuth connection failed: ${oauthError}`);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
    
    // Poll for account updates every 5 seconds when page is visible
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        loadAccounts();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/accounts/");
      setAccounts(response.data.accounts || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load accounts");
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGmail = () => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const token = localStorage.getItem("auth_token");
    if (token) {
      // Pass token as query parameter for authentication
      window.location.href = `${apiUrl}/oauth/google/?token=${encodeURIComponent(token)}`;
    } else {
      // If no token, redirect to login first
      window.location.href = "/login";
    }
  };

  const handleConnectOutlook = () => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const token = localStorage.getItem("auth_token");
    if (token) {
      // Pass token as query parameter for authentication
      window.location.href = `${apiUrl}/oauth/microsoft/?token=${encodeURIComponent(token)}`;
    } else {
      // If no token, redirect to login first
      window.location.href = "/login";
    }
  };

  const handleDisconnectAccount = async (accountId: number, emailAddress: string) => {
    if (!confirm(`Are you sure you want to disconnect ${emailAddress}?`)) {
      return;
    }

    try {
      await api.delete(`/api/accounts/disconnect/`, { data: { id: accountId } });
      loadAccounts(); // Reload accounts after disconnection
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to disconnect account");
    }
  };

  return (
    <DashboardLayout type="user">
      <div className="p-8 space-y-8">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Manage your email accounts and preferences
          </p>
        </div>

        {/* Connected Accounts */}
        <Card>
          <CardHeader>
            <CardTitle>Connected Email Accounts</CardTitle>
            <CardDescription>
              Manage your connected Gmail and Outlook accounts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="text-muted-foreground">Loading accounts...</div>
            ) : error ? (
              <div className="text-destructive">{error}</div>
            ) : accounts.length === 0 ? (
              <div className="text-center py-8 space-y-4">
                <p className="text-muted-foreground">No email accounts connected</p>
                <div className="flex gap-3 justify-center">
                  <Button onClick={handleConnectGmail}>
                    <Mail className="h-4 w-4 mr-2" />
                    Connect Gmail
                  </Button>
                  <Button onClick={handleConnectOutlook} variant="outline">
                    <Mail className="h-4 w-4 mr-2" />
                    Connect Outlook
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {accounts.map((account) => (
                  <div
                    key={account.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{account.email_address}</div>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline">{account.provider}</Badge>
                          <Badge
                            variant={
                              account.inbox_sync_status === "connected"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {account.inbox_sync_status}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={loadAccounts}
                        title="Refresh"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDisconnectAccount(account.id, account.email_address)}
                        title="Disconnect account"
                        className="text-destructive hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                <div className="pt-4 border-t">
                  <div className="flex gap-3">
                    <Button onClick={handleConnectGmail} variant="outline">
                      <Mail className="h-4 w-4 mr-2" />
                      Add Gmail
                    </Button>
                    <Button onClick={handleConnectOutlook} variant="outline">
                      <Mail className="h-4 w-4 mr-2" />
                      Add Outlook
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Settings;

