#!/bin/bash
# sync.sh - Fetch and pull latest changes from remote

set -e

echo "🔄 Syncing with remote repository..."

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Current branch: $CURRENT_BRANCH"

# Fetch from origin
echo "📥 Fetching from origin..."
git fetch origin

# Pull changes
echo "⬇️  Pulling latest changes..."
git pull origin "$CURRENT_BRANCH"

echo "✅ Sync complete!"
