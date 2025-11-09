import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import api from "@/lib/api";

interface WeeklyActivityData {
  day: string;
  spam: number;
  clean: number;
}

export const ActivityChart = () => {
  const [data, setData] = useState<WeeklyActivityData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await api.get("/api/dashboard/summary/");
        const weeklyActivity = response.data.weekly_activity || [];
        
        // If no data, show empty chart with all days
        if (weeklyActivity.length === 0) {
          const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
          setData(dayNames.map(day => ({ day, spam: 0, clean: 0 })));
        } else {
          setData(weeklyActivity);
        }
      } catch (err) {
        console.error("Failed to load activity data:", err);
        // Fallback to empty data
        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        setData(dayNames.map(day => ({ day, spam: 0, clean: 0 })));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 animate-slide-up">
        <h2 className="text-lg font-semibold mb-6">Weekly Activity</h2>
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          Loading chart data...
        </div>
      </div>
    );
  }

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
