import { Link } from "react-router-dom";

interface FooterLinkProps {
  to?: string;
  href?: string;
  children: React.ReactNode;
}

export const FooterLink = ({ to, href, children }: FooterLinkProps) => {
  const className = "text-muted-foreground hover:text-foreground transition-colors";

  if (to) {
    return (
      <li>
        <Link to={to} className={className}>
          {children}
        </Link>
      </li>
    );
  }

  return (
    <li>
      <a href={href || "#"} className={className}>
        {children}
      </a>
    </li>
  );
};

