import { Shield, Twitter, Github, Linkedin } from "lucide-react";

export const FooterBrand = () => {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-gradient-to-br from-accent to-accent/70 rounded-lg">
          <Shield className="h-5 w-5 text-accent-foreground" />
        </div>
        <span className="text-xl font-bold">InboxGuardian</span>
      </div>
      <p className="text-sm text-muted-foreground">
        Advanced email protection powered by AI. Keep your inbox clean and secure.
      </p>
      <div className="flex items-center gap-3">
        <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
          <Twitter className="h-5 w-5" />
        </a>
        <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
          <Github className="h-5 w-5" />
        </a>
        <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
          <Linkedin className="h-5 w-5" />
        </a>
      </div>
    </div>
  );
};

