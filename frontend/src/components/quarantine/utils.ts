export const getThreatColor = (threat: string): "destructive" | "outline" | "secondary" => {
  switch (threat.toLowerCase()) {
    case "phishing":
    case "malware":
      return "destructive";
    case "spam":
      return "outline";
    default:
      return "secondary";
  }
};

