# ReferWell Direct - Project Milestones

## Phase 1: Foundation (Current)
- [x] Repository scaffolding and configuration files
- [x] README.md with setup instructions
- [x] PROJECT_MILESTONES.md (this file)
- [x] OPEN_TASKS.md for task tracking
- [x] ADR/0001-architecture.md for architectural decisions
- [x] .env file for local development configuration
- [x] docker-compose.yml for local development
- [x] Makefile with development commands
- [x] pyproject.toml for Python project configuration
- [x] requirements.txt with pinned versions
- [x] .pre-commit-config.yaml for code quality
- [x] Django project "referwell" created
- [x] App modules: accounts, referrals, catalogue, matching, inbox, payments, ops
- [x] Core models with PostGIS support enabled
- [x] Database migrations for all models
- [x] Celery configuration with beat schedule
- [x] Local development environment setup
- [x] Basic UI pages with NHS.UK design system
- [x] Testing configuration (pytest + pytest-django)
- [x] Cursor rules directory setup
- [x] Feasibility filter implementation
- [x] Git repository initialization and commits
- [x] Docker services running (PostgreSQL, Redis, Mailcatcher)
- [x] Django development server working
- [x] User authentication and role-based access
- [x] REST API endpoints for users and organisations

## Phase 2: Core Matching Engine
- [x] Feasibility filter implementation
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
**Phase 1: Foundation** - ✅ Complete
- Repository scaffolding: ✅ Complete
- Django project setup: ✅ Complete
- Core models: ✅ Complete
- Development environment: ✅ Complete
- Basic UI pages: ✅ Complete
- Git repository: ✅ Complete
- PostGIS support: ✅ Complete
- Cursor rules: ✅ Complete
- Feasibility filter: ✅ Complete

**Phase 2: Core Matching Engine** - 🚧 In Progress
- Feasibility filter: ✅ Complete
- Dual retrieval system: 🚧 In Progress
- Reranking algorithm: ⏳ Pending
- Probability calibration: ⏳ Pending

## Next Actions
1. Complete dual retrieval system with vector embeddings
2. Implement reranking algorithm
3. Add probability calibration
4. Create comprehensive test suite
5. Add advanced UI features
6. Set up production configuration
