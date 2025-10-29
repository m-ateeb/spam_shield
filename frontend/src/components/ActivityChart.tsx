import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const data = [
  { day: "Mon", spam: 45, clean: 120 },
  { day: "Tue", spam: 52, clean: 135 },
  { day: "Wed", spam: 38, clean: 98 },
  { day: "Thu", spam: 61, clean: 142 },
  { day: "Fri", spam: 48, clean: 128 },
  { day: "Sat", spam: 25, clean: 65 },
  { day: "Sun", spam: 18, clean: 45 },
];

export const ActivityChart = () => {
  return (
    <div className="bg-card rounded-xl border border-border p-6 animate-slide-up">
      <h2 className="text-lg font-semibold mb-6">Weekly Activity</h2>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="day"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.5rem",
            }}
          />
          <Bar dataKey="spam" fill="hsl(var(--destructive))" radius={[8, 8, 0, 0]} />
          <Bar dataKey="clean" fill="hsl(var(--success))" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="flex items-center justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-destructive" />
          <span className="text-sm text-muted-foreground">Spam Detected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-success" />
          <span className="text-sm text-muted-foreground">Clean Emails</span>
        </div>
      </div>
    </div>
  );
};
