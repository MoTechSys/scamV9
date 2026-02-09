#!/bin/bash
# ============================================
# S-ACM Mobile UI Deployment Script
# feat/mobile-ui-overhaul
# ============================================

set -e  # Exit on error

echo "========================================"
echo " S-ACM Mobile UI Deployment"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check git status
echo -e "${BLUE}[1/5] Checking git status...${NC}"
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}Error: Not inside a git repository${NC}"
    exit 1
fi

# Step 2: Create new branch
echo -e "${BLUE}[2/5] Creating feature branch...${NC}"
BRANCH_NAME="feat/mobile-ui-overhaul"

# Check if branch already exists
if git branch --list "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
    echo "Branch $BRANCH_NAME already exists, switching to it..."
    git checkout "$BRANCH_NAME"
else
    git checkout -b "$BRANCH_NAME"
    echo -e "${GREEN}Created and switched to branch: $BRANCH_NAME${NC}"
fi

# Step 3: Stage all changes
echo -e "${BLUE}[3/5] Staging changes...${NC}"
git add static/css/mobile-app.css
git add templates/base.html
git add templates/layouts/dashboard_base.html
git add templates/core/home.html
git add deploy_mobile_ui.sh

echo "Staged files:"
git diff --cached --name-only

# Step 4: Commit
echo -e "${BLUE}[4/5] Committing changes...${NC}"
git commit -m "feat(ui): port mobile design from frontend repo

- Add comprehensive mobile-app.css with 700+ lines of mobile-first styles
- Implement fixed bottom navigation bar (flexbox, 64px height, safe-area)
- Add slide-up 'More' drawer with 3-column grid layout
- Swipe-to-close gesture support on drawer
- Compact cards (p-2/p-3, WhatsApp-style list density)
- Touch-friendly inputs (min-height 44px, no iOS zoom)
- Mobile typography scale (10px-13px body, compressed headings)
- Full-screen modals on mobile
- Horizontal scroll tabs and filter chips
- Mini stat cards in 3-column grid
- PWA meta tags (apple-mobile-web-app-capable)
- viewport-fit=cover for safe area support
- Preserve all Django template blocks and HTMX compatibility
- Hide footer on mobile for app-like experience
- Backdrop blur effects on header and bottom nav

Reference: https://github.com/MoTechSys/s-acm-frontend
Icons: Bootstrap Icons (consistent with existing project)"

echo -e "${GREEN}Commit successful!${NC}"

# Step 5: Push to remote
echo -e "${BLUE}[5/5] Pushing to remote...${NC}"
if git remote -v | grep -q "origin"; then
    git push -u origin "$BRANCH_NAME" 2>&1 || {
        echo -e "${RED}Push failed (remote may not be configured). Branch is ready locally.${NC}"
        echo "To push later: git push -u origin $BRANCH_NAME"
    }
else
    echo -e "${RED}No remote 'origin' configured. Branch created locally.${NC}"
    echo "To add remote: git remote add origin <URL>"
    echo "Then push: git push -u origin $BRANCH_NAME"
fi

echo ""
echo "========================================"
echo -e "${GREEN} Deployment Complete!${NC}"
echo "========================================"
echo ""
echo "Changes summary:"
echo "  - static/css/mobile-app.css     (NEW - 700+ lines)"
echo "  - templates/base.html           (MODIFIED - added mobile CSS)"
echo "  - templates/layouts/dashboard_base.html (MODIFIED - bottom nav + drawer)"
echo "  - templates/core/home.html      (MODIFIED - viewport + mobile CSS)"
echo ""
echo "Branch: $BRANCH_NAME"
echo "Next: Create a Pull Request to merge into main"
echo "========================================"
