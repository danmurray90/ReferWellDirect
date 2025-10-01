# GitHub Repository Setup Guide

## Prerequisites

- GitHub account
- GitHub CLI installed (`gh` command) or access to GitHub web interface

## Option 1: Using GitHub CLI (Recommended)

1. **Install GitHub CLI** (if not already installed):

   ```bash
   # macOS
   brew install gh

   # Or download from: https://cli.github.com/
   ```

2. **Authenticate with GitHub**:

   ```bash
   gh auth login
   ```

3. **Create a private repository**:

   ```bash
   cd "/Users/danmurray/Documents/Code Projects/ReferWell Direct"
   gh repo create referwell-direct --private --description "A Django-first referral matching platform for connecting patients with mental health professionals"
   ```

4. **Add the remote and push**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/referwell-direct.git
   git branch -M main
   git push -u origin main
   ```

## Option 2: Using GitHub Web Interface

1. **Go to GitHub.com** and sign in to your account

2. **Create a new repository**:

   - Click the "+" icon in the top right corner
   - Select "New repository"
   - Repository name: `referwell-direct`
   - Description: "A Django-first referral matching platform for connecting patients with mental health professionals"
   - Set to **Private**
   - Do NOT initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

3. **Add the remote and push**:
   ```bash
   cd "/Users/danmurray/Documents/Code Projects/ReferWell Direct"
   git remote add origin https://github.com/YOUR_USERNAME/referwell-direct.git
   git branch -M main
   git push -u origin main
   ```

## Option 3: Manual Setup (if you prefer)

1. **Create the repository on GitHub** (as described in Option 2)

2. **Get your repository URL** from the GitHub repository page

3. **Run these commands** (replace YOUR_USERNAME with your actual GitHub username):
   ```bash
   cd "/Users/danmurray/Documents/Code Projects/ReferWell Direct"
   git remote add origin https://github.com/YOUR_USERNAME/referwell-direct.git
   git branch -M main
   git push -u origin main
   ```

## Verification

After pushing, verify everything is working:

```bash
git remote -v
git status
git log --oneline -5
```

## Next Steps

Once the repository is set up:

1. **Enable branch protection** (optional but recommended):

   - Go to repository Settings → Branches
   - Add rule for `main` branch
   - Require pull request reviews
   - Require status checks to pass before merging

2. **Set up GitHub Actions** (optional):

   - Add `.github/workflows/ci.yml` for automated testing
   - Add `.github/workflows/pre-commit.yml` for automated linting

3. **Configure repository settings**:
   - Add topics/tags for better discoverability
   - Set up issue templates
   - Configure security settings

## Troubleshooting

If you encounter issues:

1. **Authentication problems**:

   ```bash
   gh auth status
   gh auth refresh
   ```

2. **Permission denied**:

   - Make sure you're using the correct repository URL
   - Check that the repository exists and you have write access

3. **Large files**:
   - The repository is already configured with proper .gitignore
   - If you have large files, consider using Git LFS

## Security Notes

- The repository is set to private by default
- No sensitive information (API keys, passwords) should be committed
- Use environment variables for configuration
- Consider using GitHub Secrets for CI/CD

## Git Best Practices Implemented

✅ Pre-commit hooks for code quality
✅ Conventional commit messages
✅ Proper .gitignore and .gitattributes
✅ Line ending normalization
✅ Code formatting with Black and isort
✅ Prettier for frontend files
✅ Comprehensive documentation
