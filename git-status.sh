#!/bin/bash
# git-status.sh - Show comprehensive git status

set -e

echo "📊 Git Status Summary"
echo "===================="
echo ""

# Current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Branch: $CURRENT_BRANCH"

# Check if branch is tracking a remote
REMOTE_BRANCH=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "none")
if [ "$REMOTE_BRANCH" != "none" ]; then
    echo "🔗 Tracking: $REMOTE_BRANCH"

    # Check ahead/behind
    AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    BEHIND=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")

    if [ "$AHEAD" -gt 0 ]; then
        echo "⬆️  Ahead by $AHEAD commit(s)"
    fi
    if [ "$BEHIND" -gt 0 ]; then
        echo "⬇️  Behind by $BEHIND commit(s)"
    fi
    if [ "$AHEAD" -eq 0 ] && [ "$BEHIND" -eq 0 ]; then
        echo "✅ Up to date with remote"
    fi
else
    echo "⚠️  Not tracking a remote branch"
fi

echo ""
echo "📝 Working Directory Status:"
git status --short

# Count changes
MODIFIED=$(git status --short | grep -c "^ M" || echo "0")
ADDED=$(git status --short | grep -c "^A" || echo "0")
DELETED=$(git status --short | grep -c "^D" || echo "0")
UNTRACKED=$(git status --short | grep -c "^??" || echo "0")

echo ""
echo "📈 Changes:"
echo "  Modified: $MODIFIED"
echo "  Added: $ADDED"
echo "  Deleted: $DELETED"
echo "  Untracked: $UNTRACKED"

# Recent commits
echo ""
echo "📜 Recent commits:"
git log --oneline -n 5
