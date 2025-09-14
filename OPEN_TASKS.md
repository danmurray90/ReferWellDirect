# ReferWell Direct - Open Tasks

## High Priority (Current Sprint)

### Repository Setup
- [x] Create README.md with project overview
- [x] Create PROJECT_MILESTONES.md with roadmap
- [x] Create OPEN_TASKS.md (this file)
- [x] Create ADR/0001-architecture.md
- [x] Create .env.example with all required variables
- [x] Create docker-compose.yml for local development
- [x] Create Makefile with development commands
- [x] Create pyproject.toml for Python configuration
- [x] Create requirements.txt with pinned versions
- [x] Create .pre-commit-config.yaml
- [x] Create .gitignore file

### Django Project Structure
- [ ] Create Django project "referwell"
- [ ] Create app modules: accounts, referrals, catalogue, matching, inbox, payments, ops
- [ ] Configure Django settings for development/production
- [ ] Set up URL routing
- [ ] Configure static files and media handling

### Database Models
- [ ] Create Patient model
- [ ] Create GP/Referrer model
- [ ] Create Psychologist model
- [ ] Create Organisation model
- [ ] Create Referral model
- [ ] Create Candidate model
- [ ] Create Appointment model
- [ ] Create Message/Task model
- [ ] Create AuditEvent model
- [ ] Add PostGIS and pgvector support
- [ ] Create database migrations

### Development Environment
- [ ] Set up Docker services (Postgres + PostGIS + pgvector + Redis)
- [ ] Configure Celery with beat schedule
- [ ] Create local development commands
- [ ] Set up testing framework (pytest + pytest-django)
- [ ] Configure coverage reporting

### Basic UI Pages
- [ ] Create sign-in stub page
- [ ] Create create-referral form
- [ ] Create shortlist view
- [ ] Create inbox interface
- [ ] Enable Django admin interface

### Cursor Rules
- [ ] Create .cursor/rules/ directory
- [ ] Add Django-specific rules
- [ ] Add accessibility rules
- [ ] Add testing rules
- [ ] Add code quality rules

## Medium Priority (Next Sprint)

### Matching Engine Foundation
- [ ] Implement feasibility filter
- [ ] Set up dual retrieval system
- [ ] Create reranking algorithm
- [ ] Implement probability calibration
- [ ] Add threshold routing logic

### User Interface
- [ ] Implement NHS.UK design patterns
- [ ] Add accessibility features
- [ ] Create responsive layouts
- [ ] Add form validation
- [ ] Implement error handling

### Testing
- [ ] Write model tests
- [ ] Write service tests
- [ ] Write view tests
- [ ] Add integration tests
- [ ] Set up test data fixtures

## Low Priority (Future Sprints)

### External Integrations (Stubbed)
- [ ] GOV.UK Notify adapter
- [ ] Stripe Connect adapter
- [ ] NHS Login adapter
- [ ] PDS/ODS adapter
- [ ] e-RS adapter

### Advanced Features
- [ ] Real-time notifications
- [ ] Advanced search
- [ ] Bulk operations
- [ ] Reporting and analytics
- [ ] API documentation

### Production Readiness
- [ ] Security hardening
- [ ] Performance monitoring
- [ ] Error tracking
- [ ] Backup and recovery
- [ ] Deployment automation

## Completed Tasks
- [x] Repository scaffolding and configuration files
- [x] README.md with comprehensive setup instructions
- [x] PROJECT_MILESTONES.md with detailed roadmap
- [x] OPEN_TASKS.md for task tracking

## Notes
- All external integrations must be stubbed behind feature flags
- Focus on accessibility compliance (WCAG 2.2 AA)
- Maintain comprehensive audit logging
- Follow Conventional Commits for all changes
- Write tests before or alongside code
