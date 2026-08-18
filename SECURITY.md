# Security Policy

## Reporting a vulnerability

Do **not** open a public issue for security problems. Report privately via GitHub
Security Advisories (**Security → Report a vulnerability**) on this repository, or contact
the maintainer directly. You will get an acknowledgement as soon as possible.

## Secrets

- No secrets in Git. Use `.env` (git-ignored) locally and **Azure Key Vault** for deployed
  environments. An `.env.example` documents required variables without values.
- WordPress credentials, Application Passwords, Azure OpenAI keys, and database connection
  strings are **never** committed.
- CI runs secret scanning; a push containing a detected secret should be treated as a
  compromised secret and rotated immediately.

## Scope notes

- The legacy DigitalOcean droplet is orphaned and treated as read-only; it is out of scope
  for changes and will be decommissioned after migration to Azure.
- Divi and other third-party components follow their vendors' security processes; keep the
  Divi license active so security updates continue to flow.
