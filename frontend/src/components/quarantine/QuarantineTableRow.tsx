import { useState } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TableCell, TableRow } from "@/components/ui/table";
import type { QuarantineEmail } from "./types";
import { getThreatColor } from "./utils";
import { QuarantineEmailDetails } from "./QuarantineEmailDetails";

interface QuarantineTableRowProps {
  email: QuarantineEmail;
  onRelease: (id: number) => void;
  onDelete: (id: number) => void;
}

export const QuarantineTableRow = ({ email, onRelease, onDelete }: QuarantineTableRowProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <>
      <TableRow key={email.id} className="group">
        <TableCell className="font-medium">
          {email.sender || email.sender_display || 'Unknown'}
        </TableCell>
        <TableCell className="max-w-xs truncate">
          {email.subject || '(No subject)'}
        </TableCell>
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
              variant={isExpanded ? "secondary" : "outline"}
              onClick={(e) => {
                e.stopPropagation();
                handleToggle();
              }}
            >
              {isExpanded ? "Close" : "View"}
            </Button>
            <Button 
              size="sm" 
              variant="ghost" 
              className="h-8 w-8 p-0"
              onClick={(e) => {
                e.stopPropagation();
                onRelease(email.id);
              }}
              title="Release email"
            >
              <Check className="h-4 w-4 text-green-500" />
            </Button>
            <Button 
              size="sm" 
              variant="ghost" 
              className="h-8 w-8 p-0"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(email.id);
              }}
              title="Delete permanently"
            >
              <X className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={6} className="bg-muted/30 p-0">
            <div className="p-4">
              <QuarantineEmailDetails 
                email={email} 
                isOpen={isExpanded} 
                onToggle={handleToggle}
              />
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

