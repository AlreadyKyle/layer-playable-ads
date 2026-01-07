#!/bin/bash
# save.sh - Quick commit and push all changes

set -e

# Check if a commit message was provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a commit message"
    echo "Usage: ./save.sh \"Your commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "💾 Saving changes to branch: $CURRENT_BRANCH"
echo "📝 Commit message: $COMMIT_MESSAGE"
echo ""

# Show status
echo "📊 Changes to commit:"
git status --short

# Confirm
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

# Add all changes
echo "➕ Adding all changes..."
git add -A

# Commit
echo "💾 Committing..."
git commit -m "$COMMIT_MESSAGE"

# Push
echo "⬆️  Pushing to origin/$CURRENT_BRANCH..."
git push -u origin "$CURRENT_BRANCH"

echo "✅ All changes saved and pushed!"
