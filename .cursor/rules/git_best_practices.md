# Git Best Practices for ReferWell Direct

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for consistent, meaningful commit messages:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring without changing functionality
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes
- `ci`: CI configuration changes
- `build`: Build system or dependency changes
- `revert`: Reverting a previous commit

### Scopes

Use the app/module name:

- `accounts`: User management and authentication
- `referrals`: Referral management
- `matching`: Matching algorithm and services
- `inbox`: Notifications and messaging
- `catalogue`: Psychologist profiles and services
- `payments`: Payment processing
- `ops`: Operations and monitoring
- `ci`: CI/CD pipeline
- `docs`: Documentation

### Examples

```
feat(accounts): add user profile completion tracking
fix(matching): resolve embedding calculation bug
docs(api): update authentication endpoints documentation
refactor(inbox): simplify notification service architecture
```

## Branch Naming

- `feature/description`: New features
- `fix/description`: Bug fixes
- `hotfix/description`: Critical production fixes
- `chore/description`: Maintenance tasks
- `docs/description`: Documentation updates

Examples:

- `feature/psychologist-verification`
- `fix/referral-matching-algorithm`
- `hotfix/payment-processing-error`

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

### Installed Hooks

- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML files
- **check-added-large-files**: Prevent large files
- **check-merge-conflict**: Detect merge conflict markers
- **debug-statements**: Catch debug statements
- **black**: Python code formatting
- **isort**: Python import sorting
- **prettier**: Frontend code formatting

### Running Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Skip hooks (use with caution)
git commit --no-verify -m "message"
```

## Git Configuration

### Local Configuration

```bash
# Set commit template
git config --local commit.template .gitmessage

# Line ending handling
git config --local core.autocrlf input
git config --local core.safecrlf true

# Default branch
git config --local init.defaultBranch main

# Pull strategy
git config --local pull.rebase false
```

### Global Configuration (recommended)

```bash
# User information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Default editor
git config --global core.editor "code --wait"

# Line ending handling
git config --global core.autocrlf input
git config --global core.safecrlf true
```

## Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat(scope): implement new feature"

# Push branch
git push -u origin feature/new-feature

# Create pull request on GitHub
```

### 2. Bug Fixes

```bash
# Create fix branch
git checkout -b fix/bug-description

# Make changes and commit
git add .
git commit -m "fix(scope): resolve bug description"

# Push and create PR
git push -u origin fix/bug-description
```

### 3. Hotfixes

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# Make minimal fix
git add .
git commit -m "hotfix(scope): resolve critical issue"

# Push and merge immediately
git push -u origin hotfix/critical-issue
```

## Code Review Process

### Pull Request Guidelines

1. **Clear title**: Use conventional commit format
2. **Description**: Explain what, why, and how
3. **Testing**: Include test results
4. **Screenshots**: For UI changes
5. **Breaking changes**: Clearly mark any

### Review Checklist

- [ ] Code follows project conventions
- [ ] Tests pass
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact assessed

## File Organization

### .gitignore

- Python bytecode (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `.venv/`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Environment files (`.env`, `.env.local`)
- Database files (`*.sqlite3`, `*.db`)
- Log files (`*.log`)
- Build artifacts (`build/`, `dist/`)

### .gitattributes

- Line ending normalization
- File type detection
- Binary file handling
- Language-specific settings

## Security

### Never Commit

- API keys or secrets
- Database credentials
- Private keys
- Environment files with secrets
- Personal information

### Use Environment Variables

```python
# settings.py
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

SECRET_KEY = get_env_variable('SECRET_KEY')
```

## Troubleshooting

### Common Issues

1. **Pre-commit hooks failing**:

   ```bash
   # Update hooks
   pre-commit autoupdate

   # Run specific hook
   pre-commit run black --all-files
   ```

2. **Merge conflicts**:

   ```bash
   # Resolve conflicts manually
   git status
   # Edit conflicted files
   git add .
   git commit -m "resolve merge conflicts"
   ```

3. **Accidental commits**:

   ```bash
   # Undo last commit (keep changes)
   git reset --soft HEAD~1

   # Undo last commit (discard changes)
   git reset --hard HEAD~1
   ```

4. **Wrong branch**:
   ```bash
   # Move uncommitted changes to correct branch
   git stash
   git checkout correct-branch
   git stash pop
   ```

## Best Practices Summary

1. **Commit often**: Small, focused commits
2. **Write clear messages**: Use conventional commit format
3. **Test before commit**: Run tests and linting
4. **Review before merge**: Use pull requests
5. **Keep main clean**: Only merge tested, reviewed code
6. **Use branches**: Feature branches for all changes
7. **Document changes**: Update docs with code changes
8. **Secure secrets**: Never commit sensitive information
9. **Follow conventions**: Consistent naming and formatting
10. **Automate quality**: Use pre-commit hooks and CI/CD
