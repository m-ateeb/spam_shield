import { useState, useEffect } from "react";
import api from "@/lib/api";
import type { QuarantineEmail } from "../types";

export const useQuarantine = (limit?: number) => {
  const [emails, setEmails] = useState<QuarantineEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuarantinedEmails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/quarantine/list/");
      let quarantined = response.data.quarantined || [];
      
      quarantined = quarantined.filter((q: QuarantineEmail) => q.status === 'pending');
      
      if (limit) {
        quarantined = quarantined.slice(0, limit);
      }
      
      setEmails(quarantined);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load quarantined emails");
      console.error("Quarantine error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuarantinedEmails();
  }, [limit]);

  return { emails, loading, error, reload: loadQuarantinedEmails };
};

