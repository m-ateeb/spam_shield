import { Mail, Shield, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { QuarantineEmail } from "./types";

interface QuarantineEmailDetailsProps {
  email: QuarantineEmail;
  isOpen: boolean;
  onToggle: () => void;
}

export const QuarantineEmailDetails = ({ email }: QuarantineEmailDetailsProps) => {
  const getAuthStatusBadge = (status: string) => {
    if (status === 'pass') return 'default';
    if (status === 'fail') return 'destructive';
    return 'secondary';
  };

  return (
    <div className="space-y-4">
        {/* Email Headers */}
        <div className="bg-muted/50 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <h3 className="font-semibold text-sm">Email Headers</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground font-medium">From:</span>
              <p className="mt-1 break-all">{email.sender || email.headers.from}</p>
              {email.headers.from && email.headers.from !== email.sender && (
                <p className="mt-1 text-xs text-muted-foreground break-all">
                  ({email.headers.from})
                </p>
              )}
            </div>
            {email.headers.reply_to && (
              <div>
                <span className="text-muted-foreground font-medium">Reply-To:</span>
                <p className="mt-1 break-all">{email.headers.reply_to}</p>
              </div>
            )}
            {email.headers.return_path && (
              <div>
                <span className="text-muted-foreground font-medium">Return-Path:</span>
                <p className="mt-1 break-all">{email.headers.return_path}</p>
              </div>
            )}
            <div>
              <span className="text-muted-foreground font-medium">Subject:</span>
              <p className="mt-1 break-all">{email.headers.subject}</p>
            </div>
            {email.received_at && (
              <div>
                <span className="text-muted-foreground font-medium">Received:</span>
                <p className="mt-1">{email.received_at}</p>
              </div>
            )}
          </div>
        </div>

        {/* Authentication Results */}
        <div className="bg-muted/50 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <h3 className="font-semibold text-sm">Authentication Results</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <span className="text-muted-foreground text-xs font-medium">SPF</span>
              <div className="mt-1">
                <Badge variant={getAuthStatusBadge(email.spf_result)} className="text-xs">
                  {email.spf_result}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-muted-foreground text-xs font-medium">DKIM</span>
              <div className="mt-1">
                <Badge variant={getAuthStatusBadge(email.dkim_result)} className="text-xs">
                  {email.dkim_result}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-muted-foreground text-xs font-medium">DMARC</span>
              <div className="mt-1">
                <Badge variant={getAuthStatusBadge(email.dmarc_policy)} className="text-xs">
                  {email.dmarc_policy}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-muted-foreground text-xs font-medium">Auth Score</span>
              <div className="mt-1">
                <span className={`text-sm font-semibold ${email.auth_score < 40 ? 'text-red-500' : email.auth_score < 70 ? 'text-yellow-500' : 'text-green-500'}`}>
                  {email.auth_score}/100
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Classification Reason */}
        <div className="bg-muted/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <h3 className="font-semibold text-sm">Classification Reason</h3>
          </div>
          <p className="text-sm text-muted-foreground">{email.reason}</p>
        </div>

        {/* Email Body */}
        {email.highlighted_body_html && (
          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <h3 className="font-semibold text-sm">Email Body</h3>
            </div>
            <div 
              className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-foreground prose-p:text-foreground prose-a:text-primary prose-strong:text-foreground"
              dangerouslySetInnerHTML={{ __html: email.highlighted_body_html || email.body_html }}
            />
          </div>
        )}

        {!email.highlighted_body_html && !email.body_html && (
          <div className="bg-muted/50 rounded-lg p-4 text-center text-sm text-muted-foreground">
            No email body content available
          </div>
        )}
    </div>
  );
};

