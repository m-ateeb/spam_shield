export interface RulesConfig {
  phishing_threshold: {
    auth_score_min: number;
    auth_failures_min: number;
    url_malicious_min: number;
    description: string;
  };
  suspicious_threshold: {
    auth_score_min: number;
    auth_failures_min: number;
    url_suspicious_min: number;
    description: string;
  };
  safe_threshold: {
    auth_score_min: number;
    auth_passes_min: number;
    description: string;
  };
  known_domains: {
    enabled: boolean;
    bonus_score: number;
    description: string;
  };
}

