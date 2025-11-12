import { useState, useEffect } from "react";
import api from "@/lib/api";
import type { RulesConfig } from "../types";

export const useRules = () => {
  const [rules, setRules] = useState<RulesConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    loadRules();
  }, []);

  return { rules, loading, error, setRules };
};

