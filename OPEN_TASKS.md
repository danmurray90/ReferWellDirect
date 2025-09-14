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
- [x] Create Django project "referwell"
- [x] Create app modules: accounts, referrals, catalogue, matching, inbox, payments, ops
- [x] Configure Django settings for development/production
- [x] Set up URL routing
- [x] Configure static files and media handling

### Database Models
- [x] Create Patient model
- [x] Create GP/Referrer model
- [x] Create Psychologist model
- [x] Create Organisation model
- [x] Create Referral model
- [x] Create Candidate model
- [x] Create Appointment model
- [x] Create Message/Task model
- [x] Create AuditEvent model
- [x] Add PostGIS and pgvector support (requires GDAL installation)
- [x] Create database migrations

### Development Environment
- [x] Set up Docker services (Postgres + Redis + Mailcatcher)
- [x] Configure Celery with beat schedule
- [x] Create local development commands
- [x] Set up testing framework (pytest + pytest-django)
- [x] Configure coverage reporting

### Basic UI Pages
- [x] Create home page with NHS.UK design system
- [x] Create dashboard interface
- [x] Create user authentication system
- [x] Create REST API endpoints
- [x] Enable Django admin interface

### Cursor Rules
- [x] Create .cursor/rules/ directory
- [x] Add Django-specific rules
- [x] Add accessibility rules
- [x] Add testing rules
- [x] Add code quality rules

## Medium Priority (Next Sprint)

### Matching Engine Foundation
- [x] Implement feasibility filter
- [ ] Set up dual retrieval system (vector embeddings with Sentence-Transformers)
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
- [x] Django project "referwell" created with all apps
- [x] Core models implemented for all entities
- [x] Database migrations created and applied
- [x] Docker services configured and running
- [x] Django development server working
- [x] User authentication and role-based access
- [x] REST API endpoints for users and organisations
- [x] Basic UI pages with NHS.UK design system
- [x] Git repository initialized with commits
- [x] Environment configuration (.env file)
- [x] Python dependencies installed
- [x] Superuser created for admin access
- [x] PostGIS and pgvector support enabled
- [x] Cursor rules directory with comprehensive guidelines
- [x] Feasibility filter implementation with PostGIS radius filtering

## Notes
- All external integrations must be stubbed behind feature flags
- Focus on accessibility compliance (WCAG 2.2 AA)
- Maintain comprehensive audit logging
- Follow Conventional Commits for all changes
- Write tests before or alongside code
