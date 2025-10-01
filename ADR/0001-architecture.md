# ADR-0001: Django-First Architecture

## Status

Accepted

## Context

ReferWell Direct is a referral matching platform that needs to:

- Handle complex matching algorithms with geographic and preference-based filtering
- Support multiple user types (GP, Patient, Psychologist, Admin)
- Maintain comprehensive audit trails
- Ensure accessibility compliance
- Scale to handle referral volumes
- Integrate with external services (stubbed for MVP)

## Decision

We will use a Django-first architecture with the following key components:

### Core Framework

- **Django + Django REST Framework**: Primary web framework
- **PostgreSQL + PostGIS + pgvector**: Database with geographic and vector extensions
- **Redis**: Caching and session storage
- **Celery**: Background task processing

### Architecture Principles

1. **Django-First**: Leverage Django's built-in features (ORM, admin, auth, forms)
2. **Service Layer**: Keep business logic in service classes, not models
3. **Pure Functions**: Prefer pure functions for matching algorithms
4. **Database at Edges**: Minimize database writes, keep them at service boundaries
5. **Feature Flags**: All external integrations behind feature flags (OFF by default)

### Project Structure

```
referwell/
├── accounts/          # User management
├── referrals/         # Referral creation and management
├── catalogue/         # Psychologist profiles
├── matching/          # Matching engine
├── inbox/             # Notifications and messaging
├── payments/          # Payment processing (stubbed)
└── ops/               # Audit logging and metrics
```

### Database Design

- **PostGIS**: Geographic queries using `ST_DWithin` for radius filtering
- **pgvector**: Store embeddings for similarity matching
- **Audit Trail**: Immutable `AuditEvent` model for all state changes
- **Soft Deletes**: Use flags instead of hard deletes for data retention

### Matching Pipeline

1. **Feasibility Filter**: NHS/private preference, remote/in-person, radius
2. **Retrieval**: Dual approach (BM25-like + vector similarity)
3. **Rerank**: Blend structured features with similarity scores
4. **Calibration**: Scikit-learn calibrated probability
5. **Threshold**: Route to Auto vs High-Touch queue

### External Integrations

All external services are stubbed behind feature flags:

- GOV.UK Notify (email/SMS)
- Stripe Connect (payments)
- NHS Login (authentication)
- PDS/ODS (patient data)
- e-RS (referral system)

### Testing Strategy

- **pytest + pytest-django**: Primary testing framework
- **factory_boy**: Test data generation
- **freezegun**: Time-based testing
- **Coverage**: Track test coverage for core domain logic

### Accessibility

- **WCAG 2.2 AA**: Target compliance level
- **Server-Rendered**: Use Django templates for better accessibility
- **NHS.UK Patterns**: Follow established design patterns
- **Keyboard Navigation**: Ensure full keyboard accessibility

## Consequences

### Positive

- Rapid development with Django's built-in features
- Strong ORM for complex queries
- Built-in admin interface for data management
- Excellent testing framework
- Mature ecosystem and community

### Negative

- Django's opinionated structure may limit flexibility
- Server-rendered templates may be less dynamic than SPA
- ORM performance may need optimization for large datasets

### Risks

- Over-reliance on Django's built-in features
- Potential performance bottlenecks with complex queries
- Need to ensure external integrations are properly abstracted

## Implementation Notes

- Use Django's built-in user model with custom user types
- Implement service classes for business logic
- Use Django's migration system for database changes
- Leverage Django's form system for data validation
- Use Django's admin for data management and debugging

## Alternatives Considered

- **FastAPI + SQLAlchemy**: More flexible but less opinionated
- **Django + React**: More dynamic UI but added complexity
- **Microservices**: More scalable but added operational complexity

## References

- [Django Documentation](https://docs.djangoproject.com/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [NHS.UK Design System](https://service-manual.nhs.uk/design-system)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
