import { useState } from "react";
import api from "@/lib/api";
import type { RulesConfig } from "../types";

export const useRulesActions = () => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const saveRules = async (rules: RulesConfig) => {
    try {
      setSaving(true);
      await api.post("/api/admin/rules/update/", rules);
      setSuccess("Rules updated successfully!");
      setTimeout(() => setSuccess(null), 3000);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to save rules");
    } finally {
      setSaving(false);
    }
  };

  return { saveRules, saving, error, success };
};

