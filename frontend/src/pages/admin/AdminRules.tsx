import { useEffect, useState } from "react";
import { DashboardLayout } from "../../components/DashboardLayout";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import api from "../../lib/api";
import { Save } from "lucide-react";

interface RulesConfig {
  phishing_threshold: {
    auth_score_min: number;
    auth_failures_min: number;
    url_malicious_min: number;
    description: string;
  };
  suspicious_threshold: {
    auth_score_min: number;
    auth_failures_min: number;
    url_suspicious_min: number;
    description: string;
  };
  safe_threshold: {
    auth_score_min: number;
    auth_passes_min: number;
    description: string;
  };
  known_domains: {
    enabled: boolean;
    bonus_score: number;
    description: string;
  };
}

const AdminRules = () => {
  const [rules, setRules] = useState<RulesConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/admin/rules/");
      setRules(response.data.rules);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  const saveRules = async () => {
    if (!rules) return;
    
    try {
      setSaving(true);
      await api.post("/api/admin/rules/update/", rules);
      setSuccess("Rules updated successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to save rules");
    } finally {
      setSaving(false);
    }
  };

  const updateRule = (path: string, value: any) => {
    if (!rules) return;
    const [section, key] = path.split(".");
    setRules({
      ...rules,
      [section]: {
        ...rules[section as keyof RulesConfig],
        [key]: value,
      },
    });
  };

  if (loading) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8 flex items-center justify-center min-h-[400px]">
          <div className="text-muted-foreground">Loading rules...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!rules) {
    return (
      <DashboardLayout type="admin">
        <div className="p-8">
          <div className="text-destructive">Error: {error || "No rules data available"}</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout type="admin">
      <div className="p-8 space-y-8">
        <div className="flex items-center justify-between animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold mb-2">Spam Rules Configuration</h1>
            <p className="text-muted-foreground">
              Configure spam detection rules and threat thresholds
            </p>
          </div>
          <Button onClick={saveRules} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Saving..." : "Save Rules"}
          </Button>
        </div>

        {error && (
          <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-success/10 text-success p-4 rounded-lg">
            {success}
          </div>
        )}

        {/* Phishing Threshold */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Phishing Detection Threshold</h2>
          <p className="text-sm text-muted-foreground mb-4">{rules.phishing_threshold.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Min Auth Score</Label>
              <Input
                type="number"
                value={rules.phishing_threshold.auth_score_min}
                onChange={(e) => updateRule("phishing_threshold.auth_score_min", parseInt(e.target.value))}
              />
            </div>
            <div>
              <Label>Min Auth Failures</Label>
              <Input
                type="number"
                value={rules.phishing_threshold.auth_failures_min}
                onChange={(e) => updateRule("phishing_threshold.auth_failures_min", parseInt(e.target.value))}
              />
            </div>
            <div>
              <Label>Min Malicious URLs</Label>
              <Input
                type="number"
                value={rules.phishing_threshold.url_malicious_min}
                onChange={(e) => updateRule("phishing_threshold.url_malicious_min", parseInt(e.target.value))}
              />
            </div>
          </div>
        </Card>

        {/* Suspicious Threshold */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Suspicious Email Threshold</h2>
          <p className="text-sm text-muted-foreground mb-4">{rules.suspicious_threshold.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Min Auth Score</Label>
              <Input
                type="number"
                value={rules.suspicious_threshold.auth_score_min}
                onChange={(e) => updateRule("suspicious_threshold.auth_score_min", parseInt(e.target.value))}
              />
            </div>
            <div>
              <Label>Min Auth Failures</Label>
              <Input
                type="number"
                value={rules.suspicious_threshold.auth_failures_min}
                onChange={(e) => updateRule("suspicious_threshold.auth_failures_min", parseInt(e.target.value))}
              />
            </div>
            <div>
              <Label>Min Suspicious URLs</Label>
              <Input
                type="number"
                value={rules.suspicious_threshold.url_suspicious_min}
                onChange={(e) => updateRule("suspicious_threshold.url_suspicious_min", parseInt(e.target.value))}
              />
            </div>
          </div>
        </Card>

        {/* Safe Threshold */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Safe Email Threshold</h2>
          <p className="text-sm text-muted-foreground mb-4">{rules.safe_threshold.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Min Auth Score</Label>
              <Input
                type="number"
                value={rules.safe_threshold.auth_score_min}
                onChange={(e) => updateRule("safe_threshold.auth_score_min", parseInt(e.target.value))}
              />
            </div>
            <div>
              <Label>Min Auth Passes</Label>
              <Input
                type="number"
                value={rules.safe_threshold.auth_passes_min}
                onChange={(e) => updateRule("safe_threshold.auth_passes_min", parseInt(e.target.value))}
              />
            </div>
          </div>
        </Card>

        {/* Known Domains */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Known Legitimate Domains</h2>
          <p className="text-sm text-muted-foreground mb-4">{rules.known_domains.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={rules.known_domains.enabled}
                onChange={(e) => updateRule("known_domains.enabled", e.target.checked)}
                className="h-4 w-4"
              />
              <Label>Enable Known Domain Bonus</Label>
            </div>
            <div>
              <Label>Bonus Score</Label>
              <Input
                type="number"
                value={rules.known_domains.bonus_score}
                onChange={(e) => updateRule("known_domains.bonus_score", parseInt(e.target.value))}
              />
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AdminRules;
