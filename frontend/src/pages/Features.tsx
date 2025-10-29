import { Shield, Zap, Brain, Lock, BarChart, Users, Bell, Cloud } from "lucide-react";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Detection",
    description: "Advanced machine learning algorithms analyze email patterns, content, and metadata to identify threats with 98.5% accuracy.",
    details: [
      "Natural language processing for content analysis",
      "Behavioral pattern recognition",
      "Continuous learning from new threats",
      "Multi-language support",
    ],
  },
  {
    icon: Zap,
    title: "Real-Time Protection",
    description: "Instant email scanning and quarantine with zero latency. Your inbox is protected the moment an email arrives.",
    details: [
      "Sub-second email analysis",
      "Automatic quarantine of threats",
      "No delay in email delivery",
      "24/7 monitoring",
    ],
  },
  {
    icon: Lock,
    title: "Advanced Security",
    description: "Multi-layer security architecture protects against phishing, malware, ransomware, and zero-day attacks.",
    details: [
      "URL and attachment scanning",
      "Sender reputation analysis",
      "Email spoofing detection",
      "Encrypted quarantine storage",
    ],
  },
  {
    icon: BarChart,
    title: "Smart Analytics",
    description: "Comprehensive dashboards and reports provide insights into your email security posture and threat trends.",
    details: [
      "Real-time threat monitoring",
      "Historical trend analysis",
      "Custom report generation",
      "Export to CSV/PDF",
    ],
  },
  {
    icon: Users,
    title: "Team Management",
    description: "Enterprise-grade admin controls for managing users, policies, and permissions across your organization.",
    details: [
      "Role-based access control",
      "Centralized policy management",
      "User activity tracking",
      "Bulk user operations",
    ],
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description: "Configurable alerts keep you informed about critical threats without overwhelming you with noise.",
    details: [
      "Real-time threat alerts",
      "Weekly summary reports",
      "Custom notification rules",
      "Multi-channel delivery",
    ],
  },
  {
    icon: Cloud,
    title: "Cloud-Based",
    description: "Fully cloud-hosted solution with enterprise-grade infrastructure ensures 99.9% uptime and automatic scaling.",
    details: [
      "No hardware required",
      "Automatic updates",
      "Global CDN delivery",
      "Disaster recovery",
    ],
  },
  {
    icon: Shield,
    title: "Compliance Ready",
    description: "Built-in compliance features help you meet GDPR, HIPAA, and other regulatory requirements.",
    details: [
      "Data residency options",
      "Audit logging",
      "Privacy controls",
      "Compliance reports",
    ],
  },
];

const Features = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Hero */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 rounded-full border border-accent/20">
              <Zap className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-accent">
                Powerful Features
              </span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold">
              Enterprise-Grade Email
              <span className="block text-accent mt-2">Security Features</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Everything you need to protect your inbox from modern email threats
            </p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-12 pb-24">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group animate-slide-up"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="bg-card rounded-2xl border border-border p-8 h-full hover:shadow-xl hover:border-accent/50 transition-all duration-300">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="p-3 bg-accent/10 rounded-xl group-hover:scale-110 transition-transform">
                      <feature.icon className="h-7 w-7 text-accent" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold mb-2">{feature.title}</h3>
                      <p className="text-muted-foreground">{feature.description}</p>
                    </div>
                  </div>
                  <ul className="space-y-3 ml-[68px]">
                    {feature.details.map((detail, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-accent flex-shrink-0" />
                        <span className="text-sm text-muted-foreground">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Features;
