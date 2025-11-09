import { useState, useEffect } from "react";
import { Mail, AlertTriangle, Check, X, Eye, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";

interface QuarantineEmail {
  id: number;
  email_id: number;
  sender: string;
  subject: string;
  date: string;
  threat: string;
  score: number;
  reason: string;
  status: string;
}

interface QuarantineTableProps {
  limit?: number;
  showHeader?: boolean;
}

export const QuarantineTable = ({ limit, showHeader = true }: QuarantineTableProps) => {
  const [emails, setEmails] = useState<QuarantineEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuarantinedEmails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/quarantine/list/");
      let quarantined = response.data.quarantined || [];
      
      // Filter to only show pending (not released/deleted)
      quarantined = quarantined.filter((q: QuarantineEmail) => q.status === 'pending');
      
      // Apply limit if provided
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

  const handleRelease = async (id: number) => {
    try {
      await api.post("/api/quarantine/release/", { id });
      loadQuarantinedEmails();
    } catch (err: any) {
      console.error("Release error:", err);
      alert("Failed to release email");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to permanently delete this email?")) {
      return;
    }
    try {
      await api.post("/api/quarantine/delete/", { id });
      loadQuarantinedEmails();
    } catch (err: any) {
      console.error("Delete error:", err);
      alert("Failed to delete email");
    }
  };

  const getThreatColor = (threat: string) => {
    switch (threat.toLowerCase()) {
      case "phishing":
        return "destructive" as const;
      case "malware":
        return "destructive" as const;
      case "spam":
        return "outline" as const;
      default:
        return "secondary" as const;
    }
  };

  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
        {showHeader && (
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <h2 className="text-lg font-semibold">Quarantined Emails</h2>
            </div>
          </div>
        )}
        <div className="p-8 text-center text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
        {showHeader && (
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <h2 className="text-lg font-semibold">Quarantined Emails</h2>
            </div>
          </div>
        )}
        <div className="p-8 text-center text-destructive">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
      {showHeader && (
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <h2 className="text-lg font-semibold">Quarantined Emails</h2>
            </div>
            <Button size="sm" variant="outline" onClick={loadQuarantinedEmails}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        {emails.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No quarantined emails found
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sender</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Threat</TableHead>
                <TableHead>Score</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {emails.map((email) => (
                <TableRow key={email.id} className="group">
                  <TableCell className="font-medium">{email.sender}</TableCell>
                  <TableCell className="max-w-xs truncate">{email.subject || '(No subject)'}</TableCell>
                  <TableCell className="text-muted-foreground">{email.date}</TableCell>
                  <TableCell>
                    <Badge variant={getThreatColor(email.threat)}>
                      {email.threat}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="text-sm font-medium">{email.score}%</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-8 w-8 p-0"
                        onClick={() => handleRelease(email.id)}
                        title="Release email"
                      >
                        <Check className="h-4 w-4 text-green-500" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-8 w-8 p-0"
                        onClick={() => handleDelete(email.id)}
                        title="Delete permanently"
                      >
                        <X className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};
