import { Check } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for personal use",
    features: [
      "Up to 1,000 emails/month",
      "Basic spam detection",
      "Email quarantine",
      "7-day email retention",
      "Community support",
    ],
    cta: "Get Started",
    popular: false,
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "per month",
    description: "For professionals and power users",
    features: [
      "Unlimited emails",
      "Advanced AI detection",
      "Priority quarantine",
      "30-day email retention",
      "Real-time alerts",
      "Analytics dashboard",
      "Email support",
    ],
    cta: "Start Free Trial",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "contact us",
    description: "For teams and organizations",
    features: [
      "Everything in Pro",
      "Unlimited team members",
      "Advanced admin controls",
      "Custom retention policies",
      "SSO integration",
      "API access",
      "Dedicated support",
      "SLA guarantee",
    ],
    cta: "Contact Sales",
    popular: false,
  },
];

const Pricing = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Hero */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-6 animate-fade-in">
            <h1 className="text-4xl md:text-6xl font-bold">
              Simple, Transparent
              <span className="block text-accent mt-2">Pricing</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Choose the perfect plan for your needs. All plans include a 14-day free trial.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-12 pb-24">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {plans.map((plan, index) => (
              <div
                key={index}
                className={`bg-card rounded-2xl border p-8 relative animate-slide-up ${
                  plan.popular
                    ? "border-accent shadow-xl scale-105"
                    : "border-border hover:border-accent/50"
                } transition-all duration-300`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-accent text-accent-foreground text-sm font-medium rounded-full">
                    Most Popular
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-muted-foreground text-sm mb-4">
                    {plan.description}
                  </p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground text-sm">/{plan.period}</span>
                  </div>
                </div>

                <Button
                  className={`w-full mb-6 ${
                    plan.popular
                      ? "bg-accent hover:bg-accent/90"
                      : "bg-secondary hover:bg-secondary/80"
                  }`}
                  asChild
                >
                  <Link to="/user">{plan.cta}</Link>
                </Button>

                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-accent flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* FAQ */}
          <div className="max-w-3xl mx-auto mt-24">
            <h2 className="text-3xl font-bold mb-8 text-center">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              {[
                {
                  q: "Can I switch plans later?",
                  a: "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.",
                },
                {
                  q: "What payment methods do you accept?",
                  a: "We accept all major credit cards, PayPal, and wire transfers for Enterprise plans.",
                },
                {
                  q: "Is there a free trial?",
                  a: "Yes! All paid plans come with a 14-day free trial. No credit card required.",
                },
                {
                  q: "What happens to my data if I cancel?",
                  a: "Your data is retained for 30 days after cancellation, giving you time to export if needed.",
                },
              ].map((faq, index) => (
                <div
                  key={index}
                  className="bg-card rounded-xl border border-border p-6 animate-slide-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <h3 className="font-semibold mb-2">{faq.q}</h3>
                  <p className="text-muted-foreground text-sm">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Pricing;
