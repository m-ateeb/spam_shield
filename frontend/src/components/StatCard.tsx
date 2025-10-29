import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  className?: string;
}

export const StatCard = ({
  title,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  className,
}: StatCardProps) => {
  return (
    <div
      className={cn(
        "bg-card rounded-xl border border-border p-6 transition-all duration-200 hover:shadow-lg animate-slide-up",
        className
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="text-sm font-medium text-muted-foreground">{title}</div>
        <div className="p-2 bg-muted rounded-lg">
          <Icon className="h-5 w-5 text-foreground" />
        </div>
      </div>
      
      <div className="space-y-1">
        <div className="text-3xl font-bold text-foreground">{value}</div>
        {change && (
          <div
            className={cn(
              "text-sm font-medium",
              changeType === "positive" && "text-success",
              changeType === "negative" && "text-destructive",
              changeType === "neutral" && "text-muted-foreground"
            )}
          >
            {change}
          </div>
        )}
      </div>
    </div>
  );
};
