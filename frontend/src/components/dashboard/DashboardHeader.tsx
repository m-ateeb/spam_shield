import { ReactNode } from "react";

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export const DashboardHeader = ({ title, subtitle, action }: DashboardHeaderProps) => {
  return (
    <div className="flex items-center justify-between animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold mb-2">{title}</h1>
        {subtitle && <p className="text-muted-foreground">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

