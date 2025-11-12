import { DashboardLayout } from "../DashboardLayout";

interface DashboardErrorProps {
  type: "user" | "admin";
  error: string;
}

export const DashboardError = ({ type, error }: DashboardErrorProps) => {
  return (
    <DashboardLayout type={type}>
      <div className="p-8">
        <div className="text-destructive">Error: {error}</div>
      </div>
    </DashboardLayout>
  );
};

