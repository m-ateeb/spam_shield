import { useState, useEffect } from "react";
import api from "@/lib/api";
import type { QuarantineEmail, QuarantinePagination } from "../types";

export const useQuarantine = (page: number = 1, pageSize: number = 20, limit?: number) => {
  const [emails, setEmails] = useState<QuarantineEmail[]>([]);
  const [pagination, setPagination] = useState<QuarantinePagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuarantinedEmails = async (currentPage: number = page, currentPageSize: number = pageSize) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: currentPageSize.toString(),
      });
      
      const response = await api.get(`/api/quarantine/list/?${params.toString()}`);
      let quarantined = response.data.quarantined || [];
      
      // Backend now filters by status='pending', but keep this as a safety check
      quarantined = quarantined.filter((q: QuarantineEmail) => q.status === 'pending');
      
      if (limit) {
        quarantined = quarantined.slice(0, limit);
      }
      
      setEmails(quarantined);
      
      // Set pagination if available
      if (response.data.pagination) {
        setPagination(response.data.pagination);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load quarantined emails");
      console.error("Quarantine error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuarantinedEmails(page, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize]);

  return { 
    emails, 
    pagination,
    loading, 
    error, 
    reload: () => loadQuarantinedEmails(page, pageSize),
    loadPage: (newPage: number) => loadQuarantinedEmails(newPage, pageSize)
  };
};

