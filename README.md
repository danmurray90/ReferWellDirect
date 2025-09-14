# ReferWell Direct

A Django-first referral matching platform for connecting patients with mental health professionals.

## Overview

ReferWell Direct is a local-only MVP that matches patients with appropriate psychologists based on:
- NHS/private preference
- Remote vs in-person availability
- Geographic radius (PostGIS)
- Specialisms and language requirements
- Capacity and modality preferences

## Tech Stack

- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL + PostGIS + pgvector
- **Cache**: Redis
- **Background Tasks**: Celery
- **UI**: Server-rendered templates (NHS.UK styling)
- **Testing**: pytest + pytest-django

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd referwell-direct
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start services**:
   ```bash
   make up          # Start Postgres + Redis
   make migrate     # Run database migrations
   make superuser   # Create admin user
   make dev         # Start Django + Celery worker
   ```

3. **Access the application**:
   - App: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Mailcatcher: http://localhost:1080 (if enabled)

## Development Commands

```bash
make up          # Start Docker services (Postgres + Redis)
make down        # Stop Docker services
make migrate     # Run database migrations
make superuser   # Create Django superuser
make dev         # Start Django dev server + Celery worker
make test        # Run test suite
make lint        # Run pre-commit hooks
make clean       # Clean up Docker volumes
```

## Project Structure

- `accounts/` - User management (GP, Patient, Psychologist, Admin)
- `referrals/` - Referral creation and management
- `catalogue/` - Psychologist profiles and availability
- `matching/` - Matching engine and algorithms
- `inbox/` - In-app notifications and messaging
- `payments/` - Payment processing (stubbed)
- `ops/` - Audit logging and metrics

## Key Features

- **Feasibility Filter**: NHS/private preference, remote/in-person, radius filtering
- **Matching Engine**: Dual retrieval (BM25 + vector) → rerank → calibration
- **Accessibility**: WCAG 2.2 AA compliant
- **Audit Trail**: Complete audit logging for all state changes
- **Privacy First**: No PHI in emails, in-app notifications only

## External Integrations (Stubbed)

All external services are stubbed behind feature flags (OFF by default):
- GOV.UK Notify (email/SMS)
- Stripe Connect (payments)
- NHS Login (authentication)
- PDS/ODS (patient data)
- e-RS (referral system)

## Testing

```bash
make test                    # Run all tests
make test-coverage          # Run tests with coverage
make test-models            # Run model tests only
make test-services          # Run service tests only
```

## Known Gaps

- [ ] Production deployment configuration
- [ ] External service integrations (currently stubbed)
- [ ] Advanced matching algorithms
- [ ] Mobile app interface
- [ ] Real-time notifications

## Contributing

1. Follow Conventional Commits
2. Write tests for new features
3. Ensure accessibility compliance
4. Update documentation
5. Run pre-commit hooks before committing

## License

[License details to be added]
