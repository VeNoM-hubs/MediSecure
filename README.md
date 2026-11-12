# MediSecure

A **static healthcare management and DevSecOps demonstration** portal.

MediSecure is a self-contained browser application for academic and portfolio use. It presents a hospital operations UI together with a simulated DevSecOps toolchain (GitHub, Jenkins, SonarQube, dependency scanning, Trivy, Kubernetes, and AWS CloudWatch).

> **Important:** All clinical data, security findings, and pipeline results are **fictional demonstration data**. This project does not connect to a backend, database, cloud account, or live scanner.

## Features

- Hospital dashboard with patient, doctor, appointment, and record statistics
- Patient management (search, add, remove fictional records)
- Doctor directory
- Appointment booking and status updates
- Medical records section
- DevSecOps dashboard with simulated CI/CD pipeline execution
- Security controls overview: encryption, RBAC, authentication, audit logging, vulnerability scanning
- Local persistence via `localStorage`
- Responsive layout for desktop and mobile

## Technology

- Single-file `index.html`
- Embedded CSS and vanilla JavaScript only
- No frameworks, build tools, APIs, or external dependencies

## How to run

1. Clone or download this repository.
2. Open `index.html` in a modern web browser  
   (Chrome, Edge, Firefox, or Safari).

No installation, server, or Docker setup is required.

### Demo login

| Field | Value |
| --- | --- |
| Email | `admin@medisecure.demo` |
| Password | `demo1234` |

## Project structure

```text
MediSecure/
├── index.html   # Complete application
└── README.md    # This file
```

## Notes

- Changes you make in the UI (patients, appointments, records, audit events) are stored in the browser’s `localStorage`.
- Clearing site data for the page will reset the demo to its seeded sample dataset.
- Pipeline and scanner panels are interactive simulations only and are clearly labelled as demo metrics.
