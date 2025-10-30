import { Shield, Target, Users, Award } from "lucide-react";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";

const About = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Hero */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 rounded-full border border-accent/20">
              <Shield className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-accent">
                About SpamShield
              </span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold">
              Protecting Inboxes
              <span className="block text-accent mt-2">Since 2020</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              We're on a mission to make email safe and productive for everyone
            </p>
          </div>
        </div>
      </section>

      {/* Story */}
      <section className="py-12 pb-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto space-y-16">
            {/* Our Story */}
            <div className="bg-card rounded-2xl border border-border p-8 md:p-12 animate-slide-up">
              <h2 className="text-3xl font-bold mb-6">Our Story</h2>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  SpamShield was founded in 2020 by a team of cybersecurity experts who recognized
                  the growing threat of sophisticated email attacks. What started as a simple spam
                  filter has evolved into a comprehensive email security platform powered by
                  advanced AI and machine learning.
                </p>
                <p>
                  Today, we protect over 10,000 users and businesses worldwide, blocking millions
                  of malicious emails every month. Our technology has achieved a 98.5% detection
                  rate while maintaining virtually zero false positives.
                </p>
                <p>
                  We believe that email security should be accessible to everyone, which is why
                  we've built SpamShield to be both powerful and easy to use. Our commitment to
                  innovation and user experience drives everything we do.
                </p>
              </div>
            </div>

            {/* Values */}
            <div>
              <h2 className="text-3xl font-bold mb-8 text-center">Our Values</h2>
              <div className="grid md:grid-cols-2 gap-8">
                {[
                  {
                    icon: Target,
                    title: "Innovation First",
                    description:
                      "We continuously push the boundaries of AI and machine learning to stay ahead of emerging threats.",
                  },
                  {
                    icon: Users,
                    title: "User-Centric",
                    description:
                      "Every feature we build is designed with our users' needs and experiences in mind.",
                  },
                  {
                    icon: Shield,
                    title: "Security Always",
                    description:
                      "We never compromise on security. Your data and privacy are our top priorities.",
                  },
                  {
                    icon: Award,
                    title: "Excellence",
                    description:
                      "We set the highest standards for ourselves and strive for excellence in everything we do.",
                  },
                ].map((value, index) => (
                  <div
                    key={index}
                    className="bg-card rounded-xl border border-border p-6 hover:shadow-lg hover:border-accent/50 transition-all duration-300 animate-slide-up"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="p-3 bg-accent/10 rounded-xl w-fit mb-4">
                      <value.icon className="h-6 w-6 text-accent" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{value.title}</h3>
                    <p className="text-muted-foreground">{value.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Team */}
            <div className="bg-gradient-to-br from-accent/20 via-accent/10 to-transparent rounded-2xl border border-accent/20 p-8 md:p-12 text-center animate-scale-in">
              <h2 className="text-3xl font-bold mb-4">Join Our Team</h2>
              <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
                We're always looking for talented individuals who are passionate about
                cybersecurity and want to make email safer for everyone.
              </p>
              <a
                href="#"
                className="text-accent hover:text-accent/80 font-medium inline-flex items-center gap-2"
              >
                View Open Positions →
              </a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default About;
