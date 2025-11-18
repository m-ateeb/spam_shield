export interface QuarantineEmailHeaders {
  from: string;
  reply_to: string;
  return_path: string;
  subject: string;
}

export interface QuarantineEmail {
  id: number;
  email_id: number;
  sender: string;
  subject: string;
  date: string;
  received_at?: string | null;
  threat: string;
  score: number;
  reason: string;
  status: string;
  // Full email details
  body_html: string;
  highlighted_body_html: string;
  headers: QuarantineEmailHeaders;
  auth_score: number;
  spf_result: string;
  dkim_result: string;
  dmarc_policy: string;
}

export interface QuarantinePagination {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface QuarantineTableProps {
  limit?: number;
  showHeader?: boolean;
}

