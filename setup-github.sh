#!/bin/bash

# GitHub Repository Setup Script for ReferWell Direct
# This script will create a GitHub repository and push your code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed."
        print_status "Please install it first:"
        print_status "  macOS: brew install gh"
        print_status "  Linux: https://cli.github.com/"
        exit 1
    fi
    print_success "GitHub CLI is installed"
}

# Check if user is authenticated
check_auth() {
    if ! gh auth status &> /dev/null; then
        print_error "Not authenticated with GitHub."
        print_status "Please run: gh auth login"
        exit 1
    fi
    print_success "Authenticated with GitHub"
}

# Create GitHub repository
create_repository() {
    local repo_name="referwell-direct"
    local description="A Django-first referral matching platform for connecting patients with mental health professionals"

    print_status "Creating GitHub repository: $repo_name"

    if gh repo view "$repo_name" &> /dev/null; then
        print_warning "Repository $repo_name already exists"
        read -p "Do you want to continue with the existing repository? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Exiting..."
            exit 1
        fi
    else
        gh repo create "$repo_name" \
            --private \
            --description "$description" \
            --add-readme=false
        print_success "Repository created: https://github.com/$(gh api user --jq .login)/$repo_name"
    fi
}

# Add remote and push
setup_git_remote() {
    local repo_name="referwell-direct"
    local username=$(gh api user --jq .login)

    print_status "Setting up git remote..."

    # Remove existing origin if it exists
    if git remote get-url origin &> /dev/null; then
        git remote remove origin
    fi

    # Add new origin
    git remote add origin "https://github.com/$username/$repo_name.git"
    print_success "Remote added: https://github.com/$username/$repo_name.git"

    # Push to GitHub
    print_status "Pushing code to GitHub..."
    git branch -M main
    git push -u origin main
    print_success "Code pushed to GitHub"
}

# Enable GitHub Actions
enable_actions() {
    local repo_name="referwell-direct"

    print_status "Enabling GitHub Actions..."

    # Enable Actions (this is usually enabled by default)
    gh api repos/$(gh api user --jq .login)/$repo_name/actions/permissions \
        --method PUT \
        --field enabled=true \
        --field allowed_actions=all

    print_success "GitHub Actions enabled"
}

# Set up branch protection
setup_branch_protection() {
    local repo_name="referwell-direct"

    print_status "Setting up branch protection for main branch..."

    # Create branch protection rule
    gh api repos/$(gh api user --jq .login)/$repo_name/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["CI","Pre-commit"]}' \
        --field enforce_admins=false \
        --field required_pull_request_reviews='{"required_approving_review_count":1}' \
        --field restrictions=null

    print_success "Branch protection enabled"
}

# Create initial issues and milestones
setup_project_management() {
    local repo_name="referwell-direct"

    print_status "Setting up project management..."

    # Create labels
    gh api repos/$(gh api user --jq .login)/$repo_name/labels \
        --method POST \
        --field name="bug" \
        --field color="d73a4a" \
        --field description="Something isn't working" || true

    gh api repos/$(gh api user --jq .login)/$repo_name/labels \
        --method POST \
        --field name="enhancement" \
        --field color="a2eeef" \
        --field description="New feature or request" || true

    gh api repos/$(gh api user --jq .login)/$repo_name/labels \
        --method POST \
        --field name="documentation" \
        --field color="0075ca" \
        --field description="Improvements or additions to documentation" || true

    gh api repos/$(gh api user --jq .login)/$repo_name/labels \
        --method POST \
        --field name="good first issue" \
        --field color="7057ff" \
        --field description="Good for newcomers" || true

    print_success "Project labels created"
}

# Main execution
main() {
    print_status "Starting GitHub repository setup for ReferWell Direct..."

    # Check prerequisites
    check_gh_cli
    check_auth

    # Create repository
    create_repository

    # Setup git
    setup_git_remote

    # Enable features
    enable_actions

    # Optional: Setup branch protection (uncomment if desired)
    # setup_branch_protection

    # Optional: Setup project management (uncomment if desired)
    # setup_project_management

    print_success "GitHub repository setup complete!"
    print_status "Repository URL: https://github.com/$(gh api user --jq .login)/referwell-direct"
    print_status "Actions URL: https://github.com/$(gh api user --jq .login)/referwell-direct/actions"

    print_status "Next steps:"
    print_status "1. Check the Actions tab to see your workflows running"
    print_status "2. Review the repository settings"
    print_status "3. Add collaborators if needed"
    print_status "4. Set up environment variables for deployment"
}

# Run main function
main "$@"
