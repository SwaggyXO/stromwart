# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: [hey.devashish.soni@gmail.com] (or open a private advisory)
3. Include: description, reproduction steps, potential impact

We will acknowledge within 48 hours and provide a fix timeline.

## Supported Versions

| Version | Supported |
|---------|-----------|
| master  | Yes       |

## Security Considerations

- API keys are never logged or stored in plaintext beyond local settings files (gitignored)
- Auth0 handles authentication (no custom password storage)
- LLM provider keys are transmitted only to their respective endpoints
- Simulation mode generates synthetic data only — no real user data
