import { AlertTriangle } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useQuarantine } from "./hooks/useQuarantine";
import { useQuarantineActions } from "./hooks/useQuarantineActions";
import { QuarantineHeader } from "./QuarantineHeader";
import { QuarantineTableRow } from "./QuarantineTableRow";
import type { QuarantineTableProps } from "./types";

export const QuarantineTable = ({ limit, showHeader = true }: QuarantineTableProps) => {
  const { emails, loading, error, reload } = useQuarantine(limit);
  const { handleRelease, handleDelete } = useQuarantineActions(reload);

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
      {showHeader && <QuarantineHeader onRefresh={reload} />}

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
                <QuarantineTableRow
                  key={email.id}
                  email={email}
                  onRelease={handleRelease}
                  onDelete={handleDelete}
                />
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

