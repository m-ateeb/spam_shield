import { useEffect } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { QuarantineTable } from "../components/QuarantineTable";
import { AlertTriangle } from "lucide-react";

const Quarantine = () => {
  return (
    <DashboardLayout type="user">
      <div className="p-8 space-y-8">
        <div className="animate-fade-in">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <h1 className="text-3xl font-bold">Quarantine</h1>
          </div>
          <p className="text-muted-foreground">
            Review and manage emails that have been quarantined for security reasons
          </p>
        </div>

        <QuarantineTable showHeader={false} />
      </div>
    </DashboardLayout>
  );
};

export default Quarantine;

