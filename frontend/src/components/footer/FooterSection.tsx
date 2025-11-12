import { ReactNode } from "react";

interface FooterSectionProps {
  title: string;
  children: ReactNode;
}

export const FooterSection = ({ title, children }: FooterSectionProps) => {
  return (
    <div>
      <h4 className="font-semibold mb-4">{title}</h4>
      <ul className="space-y-2 text-sm">{children}</ul>
    </div>
  );
};

