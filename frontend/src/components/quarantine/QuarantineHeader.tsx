import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuarantineHeaderProps {
  onRefresh: () => void;
}

export const QuarantineHeader = ({ onRefresh }: QuarantineHeaderProps) => {
  return (
    <div className="p-6 border-b border-border">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Quarantined Emails</h2>
        </div>
        <Button size="sm" variant="outline" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>
    </div>
  );
};

