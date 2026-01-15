#!/bin/bash
# Git Repository Setup Script for DocScope

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== DocScope Git Repository Setup ===${NC}"
echo ""

# Check if remote already exists
if git remote | grep -q origin; then
    echo -e "${YELLOW}Remote 'origin' already exists${NC}"
    git remote -v
else
    echo -e "${GREEN}Setting up remote repository...${NC}"
    echo ""
    echo "Please create a new repository on GitHub/GitLab/Bitbucket, then run:"
    echo ""
    echo -e "${BLUE}Option 1: GitHub${NC}"
    echo "git remote add origin https://github.com/yourusername/docscope.git"
    echo "git branch -M main"
    echo "git push -u origin main"
    echo ""
    echo -e "${BLUE}Option 2: GitLab${NC}"
    echo "git remote add origin https://gitlab.com/yourusername/docscope.git"
    echo "git branch -M main"
    echo "git push -u origin main"
    echo ""
    echo -e "${BLUE}Option 3: Custom Git Server${NC}"
    echo "git remote add origin git@your-server.com:docscope.git"
    echo "git branch -M main"
    echo "git push -u origin main"
fi

echo ""
echo -e "${GREEN}Repository Information:${NC}"
echo "- Current branch: $(git branch --show-current)"
echo "- Total commits: $(git rev-list --count HEAD)"
echo "- Latest commit: $(git log --oneline -1)"
echo ""

# Create tags for version
echo -e "${GREEN}Creating version tag...${NC}"
git tag -a v1.0.0 -m "Initial release: DocScope v1.0.0

Major Features:
- Multi-format document scanning
- Full-text search with Whoosh
- REST API with FastAPI
- CLI interface with Rich
- Web UI with real-time updates
- Plugin system
- Docker & Kubernetes support
- Production ready"

echo "Created tag: v1.0.0"
echo ""

echo -e "${GREEN}Repository Statistics:${NC}"
echo "- Files tracked: $(git ls-files | wc -l)"
echo "- Total lines: $(git ls-files | xargs wc -l 2>/dev/null | tail -n1 | awk '{print $1}')"
echo "- Python files: $(git ls-files '*.py' | wc -l)"
echo "- Test files: $(git ls-files 'tests/*.py' | wc -l)"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "1. Create repository on your Git hosting platform"
echo "2. Add remote origin using one of the commands above"
echo "3. Push code: git push -u origin main"
echo "4. Push tags: git push --tags"
echo "5. Set up CI/CD pipelines (GitHub Actions, GitLab CI, etc.)"
echo "6. Configure branch protection rules"
echo "7. Add collaborators/team members"
echo ""

echo -e "${GREEN}✅ DocScope is ready to be pushed to your remote repository!${NC}"