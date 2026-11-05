# Architecture

```mermaid
flowchart TB
  Browser[Browser SPA] -->|HTTPS / JWT| API[FastAPI /api/v1]
  API --> Auth[Auth + RBAC]
  API --> Appt[Appointments + Slots]
  API --> Records[Medical Records]
  API --> Notify[Notifications]
  API --> Audit[Audit Logger]
  Auth --> DB[(PostgreSQL)]
  Appt --> DB
  Records --> DB
  Notify --> DB
  Audit --> DB
```

## Data flow

```mermaid
sequenceDiagram
  participant P as Patient
  participant UI as Frontend
  participant API as Backend
  participant DB as Postgres
  P->>UI: Login
  UI->>API: POST /auth/login
  API->>DB: Verify Argon2 + lockout state
  API-->>UI: access + refresh tokens
  UI->>API: Book slot
  API->>DB: Transaction + double-book check
  API->>DB: Audit + notification
```

## DevSecOps pipeline

```mermaid
flowchart LR
  Commit --> Jenkins
  Jenkins --> Tests
  Tests --> SonarQube
  Tests --> TrivyFS[Trivy FS]
  TrivyFS --> Build[Docker Build]
  Build --> TrivyImg[Trivy Image]
  TrivyImg --> Registry
  Registry --> K3s
```

## Module boundaries

Auth, Patients, Doctors, Appointments, Medical Records, Notifications, Audit, Admin — each exposed via versioned REST routers with shared deps for DB/authz.
