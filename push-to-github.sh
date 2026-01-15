#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== DocScope GitHub Push Assistant ===${NC}"
echo ""

# Check if remote already exists
if git remote | grep -q origin; then
    echo -e "${YELLOW}Remote 'origin' already exists. Current configuration:${NC}"
    git remote -v
    echo ""
    read -p "Do you want to remove and reconfigure it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
        echo -e "${GREEN}Removed existing origin${NC}"
    else
        echo -e "${YELLOW}Using existing remote configuration${NC}"
        SKIP_REMOTE=true
    fi
fi

if [ "$SKIP_REMOTE" != "true" ]; then
    echo ""
    echo -e "${BLUE}Please enter your GitHub username:${NC}"
    read -p "GitHub Username: " GITHUB_USERNAME
    
    if [ -z "$GITHUB_USERNAME" ]; then
        echo -e "${RED}Error: GitHub username cannot be empty${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}Choose connection method:${NC}"
    echo "1) HTTPS (recommended for most users)"
    echo "2) SSH (requires SSH keys to be configured)"
    read -p "Enter choice (1 or 2): " CONNECTION_METHOD
    
    case $CONNECTION_METHOD in
        1)
            REMOTE_URL="https://github.com/${GITHUB_USERNAME}/docscope.git"
            echo -e "${GREEN}Using HTTPS URL: $REMOTE_URL${NC}"
            ;;
        2)
            REMOTE_URL="git@github.com:${GITHUB_USERNAME}/docscope.git"
            echo -e "${GREEN}Using SSH URL: $REMOTE_URL${NC}"
            ;;
        *)
            echo -e "${RED}Invalid choice. Using HTTPS by default.${NC}"
            REMOTE_URL="https://github.com/${GITHUB_USERNAME}/docscope.git"
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}Adding remote origin...${NC}"
    git remote add origin "$REMOTE_URL"
    echo -e "${GREEN}✓ Remote added successfully${NC}"
fi

echo ""
echo -e "${BLUE}Current Git Status:${NC}"
echo "- Branch: $(git branch --show-current)"
echo "- Commits: $(git rev-list --count HEAD)"
echo "- Remote: $(git remote get-url origin 2>/dev/null || echo 'Not configured')"

echo ""
echo -e "${YELLOW}IMPORTANT: Before pushing, make sure you have:${NC}"
echo "1. Created the 'docscope' repository on GitHub"
echo "2. NOT initialized it with any files (README, license, or .gitignore)"

echo ""
read -p "Have you created the empty repository on GitHub? (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Please create the repository first:${NC}"
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: docscope"
    echo "3. Leave all initialization options UNCHECKED"
    echo "4. Click 'Create repository'"
    echo "5. Run this script again"
    exit 0
fi

echo ""
echo -e "${BLUE}Pushing to GitHub...${NC}"

# Ensure we're on main branch
git branch -M main

# Push the main branch
echo -e "${BLUE}Pushing main branch...${NC}"
if git push -u origin main; then
    echo -e "${GREEN}✓ Main branch pushed successfully${NC}"
else
    echo -e "${RED}✗ Failed to push main branch${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. If authentication failed (HTTPS):"
    echo "   - You may need to use a Personal Access Token instead of password"
    echo "   - Create one at: https://github.com/settings/tokens"
    echo "2. If permission denied (SSH):"
    echo "   - Make sure your SSH keys are configured"
    echo "   - Test with: ssh -T git@github.com"
    echo "3. If repository not found:"
    echo "   - Make sure you created 'docscope' repository on GitHub"
    echo "   - Check the spelling and your username"
    exit 1
fi

# Push tags
echo ""
echo -e "${BLUE}Pushing tags...${NC}"
if git push --tags; then
    echo -e "${GREEN}✓ Tags pushed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Failed to push tags, but main branch was pushed${NC}"
fi

echo ""
echo -e "${GREEN}=== SUCCESS! ===${NC}"
echo ""
echo -e "${BLUE}Your DocScope repository is now live at:${NC}"
echo -e "${GREEN}https://github.com/${GITHUB_USERNAME}/docscope${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Visit your repository on GitHub"
echo "2. Add a description and topics (tags)"
echo "3. Configure GitHub Pages if desired"
echo "4. Set up branch protection rules"
echo "5. Configure GitHub Actions secrets for CI/CD"
echo ""
echo -e "${GREEN}✨ Congratulations! DocScope is now on GitHub! ✨${NC}"