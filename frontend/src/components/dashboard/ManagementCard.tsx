import { LucideIcon } from "lucide-react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";

interface ManagementCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  buttonText: string;
  onClick: () => void;
  iconBg?: string;
  iconColor?: string;
}

export const ManagementCard = ({
  icon: Icon,
  title,
  description,
  buttonText,
  onClick,
  iconBg = "bg-accent/10",
  iconColor = "text-accent",
}: ManagementCardProps) => {
  return (
    <Card className="p-6 hover:shadow-lg transition-all duration-200 animate-slide-up border-border">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-3 ${iconBg} rounded-lg`}>
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
        <h3 className="font-semibold text-lg">{title}</h3>
      </div>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      <Button variant="outline" className="w-full" onClick={onClick}>
        {buttonText}
      </Button>
    </Card>
  );
};

