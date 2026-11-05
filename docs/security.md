# MediSecure security controls

## Implemented

- Argon2 password hashing (no plaintext storage)
- Short-lived JWT access tokens + rotating refresh tokens (hashed at rest)
- RBAC + object-level authorization (IDOR protections)
- Login failure tracking and temporary lockout
- Auth endpoint rate limiting
- CORS allowlisting via environment
- Security response headers
- Request correlation IDs
- Centralized exception handling (no stack traces in production)
- Audit logging without secrets/tokens/full clinical content
- Pydantic validation + SQLAlchemy parameterization
- Non-root Docker users; secrets via env/K8s Secret placeholders

## Checklist

| Control | Status |
| --- | --- |
| Argon2 hashing | Implemented |
| Refresh token rotation/revocation | Implemented |
| IDOR prevention tests | Implemented |
| Rate limiting (auth) | Implemented |
| Security headers | Implemented |
| `/health` + `/ready` | Implemented |
| Trivy scripts | Prepared |
| SonarQube properties | Prepared |
| K8s NetworkPolicy / RBAC | Prepared |

## Future placeholders

- Redis-backed distributed rate limiting
- External Secrets / Vault operator
- WAF / Ingress TLS termination policies
- Prometheus exporters beyond `/metrics` stub
