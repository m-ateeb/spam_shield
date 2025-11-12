import { FooterBrand } from "./footer/FooterBrand";
import { FooterSection } from "./footer/FooterSection";
import { FooterLink } from "./footer/FooterLink";

export const Footer = () => {
  return (
    <footer className="border-t border-border bg-card">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <FooterBrand />

          <FooterSection title="Product">
            <FooterLink to="/features">Features</FooterLink>
            <FooterLink to="/pricing">Pricing</FooterLink>
            <FooterLink to="/user">Dashboard</FooterLink>
          </FooterSection>

          <FooterSection title="Company">
            <FooterLink to="/about">About Us</FooterLink>
            <FooterLink to="/contact">Contact</FooterLink>
            <FooterLink href="#">Careers</FooterLink>
          </FooterSection>

          <FooterSection title="Legal">
            <FooterLink href="#">Privacy Policy</FooterLink>
            <FooterLink href="#">Terms of Service</FooterLink>
            <FooterLink href="#">Cookie Policy</FooterLink>
          </FooterSection>
        </div>

        <div className="border-t border-border mt-8 pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2025 InboxGuardian. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
