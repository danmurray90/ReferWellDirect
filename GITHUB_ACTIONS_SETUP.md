# GitHub Actions CI/CD Pipeline Setup

This document describes the comprehensive GitHub Actions workflows set up for the ReferWell Direct project.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Make sure you have GitHub CLI installed
brew install gh  # macOS
# or download from https://cli.github.com/

# Authenticate with GitHub
gh auth login

# Run the automated setup script
./setup-github.sh
```

### Option 2: Manual Setup

1. Create a new private repository on GitHub named `referwell-direct`
2. Add the remote and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/referwell-direct.git
   git branch -M main
   git push -u origin main
   ```

## 📋 Workflows Overview

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)

**Triggers**: Push to main/develop, Pull requests
**Features**:

- Multi-Python version testing (3.11, 3.12)
- PostgreSQL + PostGIS + Redis services
- Pre-commit hooks validation
- Test execution with coverage
- Security scanning (Bandit, Safety)
- Package building

### 2. **Pre-commit Validation** (`.github/workflows/pre-commit.yml`)

**Triggers**: Push to main/develop, Pull requests
**Features**:

- Runs all pre-commit hooks
- Ensures code quality before merge
- Fast feedback loop

### 3. **Code Quality** (`.github/workflows/quality.yml`)

**Triggers**: Push to main/develop, Pull requests
**Features**:

- Coverage reporting with Codecov integration
- Multiple linting tools (Black, isort, flake8, mypy, pylint)
- Code complexity analysis (radon, xenon)
- Detailed quality reports

### 4. **Security Scanning** (`.github/workflows/security.yml`)

**Triggers**: Weekly schedule, Push to main, Pull requests
**Features**:

- Dependency vulnerability scanning (Safety)
- Code security analysis (Bandit)
- SAST scanning (Semgrep)
- Dependency review for PRs
- Automated security reports

### 5. **Database Operations** (`.github/workflows/database.yml`)

**Triggers**: Push to main/develop, Pull requests, Manual
**Features**:

- Migration conflict detection
- Database schema validation
- PostGIS and pgvector extension checks
- Migration safety validation

### 6. **Deployment** (`.github/workflows/deploy.yml`)

**Triggers**: Push to main, Manual
**Features**:

- Production deployment preparation
- Static file collection
- Deployment package creation
- SSH deployment (configurable)

### 7. **Dependency Updates** (`.github/workflows/dependencies.yml`)

**Triggers**: Weekly schedule, Manual
**Features**:

- Automated dependency updates
- Pull request creation for updates
- Safety validation

## 🔧 Configuration

### Environment Variables

Set these in your GitHub repository settings (Settings → Secrets and variables → Actions):

#### Required

- `SECRET_KEY`: Django secret key for testing

#### Optional (for deployment)

- `HOST`: Production server hostname
- `USERNAME`: SSH username
- `SSH_KEY`: Private SSH key for deployment

### Repository Settings

1. **Branch Protection**: Enable for main branch

   - Require status checks: CI, Pre-commit
   - Require pull request reviews
   - Require up-to-date branches

2. **Actions Permissions**:
   - Allow all actions and reusable workflows
   - Allow GitHub Actions to create and approve pull requests

## 📊 Monitoring and Reports

### Coverage Reports

- **Codecov Integration**: Automatic coverage reporting
- **Coverage Threshold**: 80% minimum
- **Reports**: Available in Actions artifacts

### Security Reports

- **Bandit**: Python security issues
- **Safety**: Dependency vulnerabilities
- **Semgrep**: SAST security scanning
- **Dependency Review**: PR dependency analysis

### Quality Metrics

- **Code Complexity**: Radon and Xenon analysis
- **Linting**: Multiple tools for comprehensive coverage
- **Formatting**: Black and isort consistency

## 🛠️ Local Development

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Testing

```bash
# Run tests locally
python manage.py test --settings=referwell.settings.development

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy . --ignore-missing-imports

# Security scan
bandit -r .
safety check
```

## 🔄 Workflow Customization

### Adding New Workflows

1. Create new `.yml` file in `.github/workflows/`
2. Follow the existing patterns for consistency
3. Test locally before pushing

### Modifying Existing Workflows

1. Update the workflow file
2. Test with a feature branch
3. Merge to main when validated

### Environment-Specific Deployments

Edit `.github/workflows/deploy.yml` to add:

- Staging environment deployment
- Production environment deployment
- Environment-specific configurations

## 🚨 Troubleshooting

### Common Issues

1. **Workflow Fails on Push**

   - Check pre-commit hooks locally first
   - Ensure all tests pass locally
   - Verify environment variables are set

2. **Database Connection Issues**

   - Check PostgreSQL service configuration
   - Verify connection strings
   - Ensure PostGIS extension is available

3. **Security Scan Failures**

   - Review security reports
   - Update dependencies if needed
   - Address security issues in code

4. **Coverage Below Threshold**
   - Add more tests
   - Check coverage configuration
   - Review uncovered code

### Debugging

- Check Actions logs for detailed error messages
- Use `act` to run workflows locally
- Enable debug logging in workflows

## 📈 Performance Optimization

### Workflow Optimization

- Use caching for dependencies
- Parallel job execution
- Conditional job execution
- Matrix strategies for multiple versions

### Resource Management

- Appropriate runner types
- Timeout configurations
- Resource limits

## 🔐 Security Considerations

### Secrets Management

- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Limit secret access scope

### Code Security

- Regular dependency updates
- Security scanning in CI/CD
- Code review requirements
- Branch protection rules

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django Testing Guide](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Pre-commit Hooks](https://pre-commit.com/)
- [Codecov Integration](https://docs.codecov.com/)

## 🤝 Contributing

When contributing to this project:

1. Create a feature branch
2. Make your changes
3. Ensure all workflows pass
4. Create a pull request
5. Address any review feedback

The CI/CD pipeline will automatically validate your changes and provide feedback on code quality, security, and functionality.
