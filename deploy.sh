#!/bin/bash

echo "🚀 Starting deployment process..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ No remote origin found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/yourusername/yourrepo.git"
    exit 1
fi

echo "✅ Git repository configured"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Deploy to production"
git push origin main

echo "✅ Code pushed to GitHub"
echo ""
echo "🎯 Next steps:"
echo "1. Deploy backend on Render:"
echo "   - Go to https://dashboard.render.com/"
echo "   - Create new Web Service"
echo "   - Connect your GitHub repo"
echo "   - Use build command: pip install -r requirements.txt"
echo "   - Use start command: uvicorn auth_backend:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "2. Deploy frontend on Vercel:"
echo "   - Go to https://vercel.com/dashboard"
echo "   - Create new project"
echo "   - Import your GitHub repo"
echo "   - Set root directory to 'frontend'"
echo "   - Framework preset: Vite"
echo ""
echo "3. Update CORS and API URLs:"
echo "   - Update auth_backend.py with your Vercel domain"
echo "   - Update vercel.json with your Render backend URL"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions" 