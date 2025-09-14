# ReferWell Direct - Project Milestones

## Phase 1: Foundation (Current)
- [x] Repository scaffolding and configuration files
- [x] README.md with setup instructions
- [x] PROJECT_MILESTONES.md (this file)
- [x] OPEN_TASKS.md for task tracking
- [x] ADR/0001-architecture.md for architectural decisions
- [x] .env.example with all required environment variables
- [x] docker-compose.yml for local development
- [x] Makefile with development commands
- [x] pyproject.toml for Python project configuration
- [x] requirements.txt with pinned versions
- [x] .pre-commit-config.yaml for code quality
- [x] Django project "referwell" created
- [x] App modules: accounts, referrals, catalogue, matching, inbox, payments, ops
- [x] Core models with PostGIS + pgvector support
- [x] Database migrations for all models
- [x] Celery configuration with beat schedule
- [x] Local development environment setup
- [x] Basic UI pages (sign-in, create-referral, shortlist, inbox, admin)
- [x] Testing configuration (pytest + pytest-django)
- [x] Cursor rules directory setup

## Phase 2: Core Matching Engine
- [ ] Feasibility filter implementation
- [ ] Dual retrieval system (BM25 + vector)
- [ ] Reranking algorithm with structured features
- [ ] Probability calibration (isotonic/Platt)
- [ ] Threshold routing to High-Touch queue
- [ ] Matching explanation generation
- [ ] Performance optimization

## Phase 3: User Experience
- [ ] NHS.UK design system integration
- [ ] Accessibility compliance (WCAG 2.2 AA)
- [ ] Mobile-responsive design
- [ ] Progressive disclosure patterns
- [ ] Error handling and validation
- [ ] User onboarding flow

## Phase 4: Advanced Features
- [ ] Real-time notifications
- [ ] Advanced search and filtering
- [ ] Bulk operations
- [ ] Reporting and analytics
- [ ] Data export capabilities
- [ ] API documentation

## Phase 5: External Integrations (Stubbed)
- [ ] GOV.UK Notify adapter (stubbed)
- [ ] Stripe Connect adapter (stubbed)
- [ ] NHS Login adapter (stubbed)
- [ ] PDS/ODS adapter (stubbed)
- [ ] e-RS adapter (stubbed)
- [ ] Feature flag management
- [ ] Integration testing

## Phase 6: Production Readiness
- [ ] Security hardening
- [ ] Performance monitoring
- [ ] Error tracking
- [ ] Backup and recovery
- [ ] Deployment automation
- [ ] Documentation completion

## Current Status
**Phase 1: Foundation** - In Progress
- Repository scaffolding: ✅ Complete
- Django project setup: 🔄 In Progress
- Core models: 🔄 In Progress
- Development environment: 🔄 In Progress

## Next Actions
1. Complete Django project structure
2. Implement core models with PostGIS support
3. Set up database migrations
4. Configure Celery and Redis
5. Create basic UI pages
6. Set up testing framework
