import { Link } from "react-router-dom";
import { Shield, ArrowRight, CheckCircle, Zap, Lock, BarChart } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";

const Home = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-accent/10 via-transparent to-transparent" />
        <div className="container mx-auto px-4 py-24 md:py-32 relative">
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 rounded-full border border-accent/20 backdrop-blur-sm">
              <Shield className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-accent">
                AI-Powered Email Protection
              </span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
              Stop Spam Before It
              <span className="block bg-gradient-to-r from-accent to-accent/70 bg-clip-text text-transparent mt-2">
                Reaches Your Inbox
              </span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              SpamShield's advanced AI detects and quarantines malicious emails in real-time,
              protecting you from phishing, malware, and unwanted messages with 98.5% accuracy.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Button
                size="lg"
                className="bg-accent hover:bg-accent/90 text-accent-foreground group"
                asChild
              >
                <Link to="/pricing">
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link to="/features">View Features</Link>
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto pt-12">
              {[
                { value: "1.2M+", label: "Emails Protected" },
                { value: "98.5%", label: "Detection Rate" },
                { value: "10k+", label: "Active Users" },
              ].map((stat, index) => (
                <div key={index} className="space-y-1">
                  <div className="text-3xl md:text-4xl font-bold text-accent">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-slide-up">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to Stay Protected
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Comprehensive email security with advanced features designed for modern threats
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                icon: Zap,
                title: "Real-Time Detection",
                description: "Instant analysis and quarantine of suspicious emails using advanced AI algorithms",
              },
              {
                icon: Lock,
                title: "Advanced Security",
                description: "Multi-layer protection against phishing, malware, and zero-day threats",
              },
              {
                icon: BarChart,
                title: "Smart Analytics",
                description: "Detailed insights and trends about your email security patterns",
              },
              {
                icon: Shield,
                title: "Auto-Learning",
                description: "Continuously improves detection accuracy based on new threat patterns",
              },
              {
                icon: CheckCircle,
                title: "Easy Management",
                description: "Simple interface to review, restore, or permanently delete quarantined items",
              },
              {
                icon: ArrowRight,
                title: "Zero False Positives",
                description: "Intelligent filtering ensures important emails always reach your inbox",
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="bg-card p-8 rounded-2xl border border-border hover:shadow-xl hover:border-accent/50 transition-all duration-300 group animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="p-3 bg-accent/10 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="h-6 w-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto bg-gradient-to-br from-accent/20 via-accent/10 to-transparent rounded-3xl border border-accent/20 p-12 text-center space-y-6 animate-scale-in">
            <h2 className="text-3xl md:text-4xl font-bold">
              Ready to Secure Your Inbox?
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Join thousands of users protecting their email with SpamShield.
              Start your free trial today, no credit card required.
            </p>
            <Button
              size="lg"
              className="bg-accent hover:bg-accent/90 text-accent-foreground"
              asChild
            >
              <Link to="/pricing">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;
