export interface QuarantineEmail {
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

export interface QuarantineTableProps {
  limit?: number;
  showHeader?: boolean;
}

