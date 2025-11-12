import { DashboardLayout } from "../DashboardLayout";

interface DashboardLoadingProps {
  type: "user" | "admin";
  message?: string;
}

export const DashboardLoading = ({ type, message = "Loading dashboard..." }: DashboardLoadingProps) => {
  return (
    <DashboardLayout type={type}>
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-muted-foreground">{message}</div>
      </div>
    </DashboardLayout>
  );
};

