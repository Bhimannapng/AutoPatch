#!/usr/bin/env bash
set -e

echo "=========================================="
echo "🚀 AutoPatch 2.0 Full Deployment Pipeline"
echo "=========================================="

PROJECT_DIR="/Users/bhimanna/Desktop/AutoPatch"
cd "$PROJECT_DIR"

# 1. Frontend Build
echo "📦 Building optimized React frontend..."
cd frontend
npm run build
cd ..

# 2. Firebase Hosting Deployment
echo "🌐 Deploying to Firebase Hosting (autopatch-ai-2026)..."
firebase deploy --only hosting --project autopatch-ai-2026

# 3. Git commit & sync if changes exist
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Committing updated code to git..."
    git add .
    git commit -m "Auto-deploy update: $(date '+%Y-%m-%d %H:%M:%S')"
fi

echo "=========================================="
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "Live Web App: https://autopatch-ai-2026.web.app"
echo "=========================================="
