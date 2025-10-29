import { useState } from "react";
import { Mail, AlertTriangle, Check, X, Eye } from "lucide-react";
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

interface QuarantineEmail {
  id: string;
  sender: string;
  subject: string;
  date: string;
  threat: string;
  score: number;
}

const mockEmails: QuarantineEmail[] = [
  {
    id: "1",
    sender: "suspicious@phishing.com",
    subject: "URGENT: Verify Your Account Now!!!",
    date: "2025-01-15 10:32",
    threat: "Phishing",
    score: 98,
  },
  {
    id: "2",
    sender: "no-reply@spam-deals.net",
    subject: "🎁 You've Won $1,000,000!",
    date: "2025-01-15 09:15",
    threat: "Spam",
    score: 95,
  },
  {
    id: "3",
    sender: "malware@virus.org",
    subject: "Invoice_2025.pdf.exe",
    date: "2025-01-14 16:45",
    threat: "Malware",
    score: 99,
  },
  {
    id: "4",
    sender: "scam@fake-bank.com",
    subject: "Security Alert: Unusual Activity",
    date: "2025-01-14 14:20",
    threat: "Phishing",
    score: 97,
  },
];

export const QuarantineTable = () => {
  const [emails] = useState<QuarantineEmail[]>(mockEmails);

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

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Quarantined Emails</h2>
        </div>
      </div>

      <div className="overflow-x-auto">
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
                <TableCell className="max-w-xs truncate">{email.subject}</TableCell>
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
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                      <Check className="h-4 w-4 text-success" />
                    </Button>
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                      <X className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
