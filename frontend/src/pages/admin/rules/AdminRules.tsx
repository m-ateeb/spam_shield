import { DashboardLayout } from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";
import { useRules } from "./hooks/useRules";
import { useRulesActions } from "./hooks/useRulesActions";
import { RuleSection } from "./components/RuleSection";
import type { RulesConfig } from "./types";

const AdminRules = () => {
  const { rules, loading, error: loadError, setRules } = useRules();
  const { saveRules, saving, error: saveError, success } = useRulesActions();

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

  const handleSave = () => {
    if (!rules) return;
    saveRules(rules);
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
          <div className="text-destructive">Error: {loadError || "No rules data available"}</div>
        </div>
      </DashboardLayout>
    );
  }

  const error = loadError || saveError;

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
          <Button onClick={handleSave} disabled={saving}>
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

        <RuleSection
          title="Phishing Detection Threshold"
          description={rules.phishing_threshold.description}
          sectionKey="phishing_threshold"
          rules={rules}
          onUpdate={updateRule}
          fields={[
            { key: "auth_score_min", label: "Min Auth Score" },
            { key: "auth_failures_min", label: "Min Auth Failures" },
            { key: "url_malicious_min", label: "Min Malicious URLs" },
          ]}
        />

        <RuleSection
          title="Suspicious Email Threshold"
          description={rules.suspicious_threshold.description}
          sectionKey="suspicious_threshold"
          rules={rules}
          onUpdate={updateRule}
          fields={[
            { key: "auth_score_min", label: "Min Auth Score" },
            { key: "auth_failures_min", label: "Min Auth Failures" },
            { key: "url_suspicious_min", label: "Min Suspicious URLs" },
          ]}
        />

        <RuleSection
          title="Safe Email Threshold"
          description={rules.safe_threshold.description}
          sectionKey="safe_threshold"
          rules={rules}
          onUpdate={updateRule}
          fields={[
            { key: "auth_score_min", label: "Min Auth Score" },
            { key: "auth_passes_min", label: "Min Auth Passes" },
          ]}
        />

        <RuleSection
          title="Known Legitimate Domains"
          description={rules.known_domains.description}
          sectionKey="known_domains"
          rules={rules}
          onUpdate={updateRule}
          fields={[
            { key: "enabled", label: "Enable Known Domain Bonus", type: "checkbox" },
            { key: "bonus_score", label: "Bonus Score" },
          ]}
        />
      </div>
    </DashboardLayout>
  );
};

export default AdminRules;

