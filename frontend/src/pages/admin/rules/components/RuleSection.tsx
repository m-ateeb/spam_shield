import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { RulesConfig } from "../types";

interface RuleSectionProps {
  title: string;
  description: string;
  sectionKey: keyof RulesConfig;
  rules: RulesConfig;
  onUpdate: (path: string, value: any) => void;
  fields: Array<{
    key: string;
    label: string;
    type?: "number" | "checkbox";
  }>;
}

export const RuleSection = ({ title, description, sectionKey, rules, onUpdate, fields }: RuleSectionProps) => {
  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold mb-4">{title}</h2>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      <div className={`grid grid-cols-1 ${fields.length === 2 ? 'md:grid-cols-2' : fields.length === 3 ? 'md:grid-cols-3' : 'md:grid-cols-4'} gap-4`}>
        {fields.map((field) => {
          const path = `${sectionKey}.${field.key}`;
          const value = rules[sectionKey][field.key as keyof typeof rules[typeof sectionKey]];

          if (field.type === "checkbox") {
            return (
              <div key={field.key} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={value as boolean}
                  onChange={(e) => onUpdate(path, e.target.checked)}
                  className="h-4 w-4"
                />
                <Label>{field.label}</Label>
              </div>
            );
          }

          return (
            <div key={field.key}>
              <Label>{field.label}</Label>
              <Input
                type="number"
                value={value as number}
                onChange={(e) => onUpdate(path, parseInt(e.target.value))}
              />
            </div>
          );
        })}
      </div>
    </Card>
  );
};

