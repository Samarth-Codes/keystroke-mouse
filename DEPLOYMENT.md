# Deployment Guide

This guide will help you deploy your keystroke dynamics authentication system on Vercel (frontend) and Render (backend).

## Prerequisites

1. GitHub account
2. Vercel account (free tier available)
3. Render account (free tier available)

## Backend Deployment (Render)

### Step 1: Prepare Backend
1. Make sure your backend files are in the root directory:
   - `auth_backend.py` - Main FastAPI application
   - `requirements.txt` - Python dependencies
   - `render.yaml` - Render configuration
   - `Procfile` - Alternative deployment configuration

### Step 2: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `keystroke-auth-backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn auth_backend:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"
6. Wait for deployment to complete
7. Copy the generated URL (e.g., `https://your-app-name.onrender.com`)

### Step 3: Update CORS Configuration
1. Update the CORS origins in `auth_backend.py`:
   ```python
   allow_origins=[
       "https://your-frontend-domain.vercel.app",  # Your Vercel domain
       "http://localhost:5173",
       "http://localhost:3000",
   ],
   ```

## Frontend Deployment (Vercel)

### Step 1: Prepare Frontend
1. Navigate to the `frontend` directory
2. Make sure you have the following files:
   - `package.json` - Dependencies and scripts
   - `vite.config.js` - Vite configuration
   - `vercel.json` - Vercel configuration
   - `src/App.jsx` - Main React component

### Step 2: Update API Configuration
1. Update `vercel.json` with your Render backend URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/(.*)",
         "destination": "https://your-backend-domain.onrender.com/$1"
       }
     ]
   }
   ```

### Step 3: Deploy on Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click "Deploy"
6. Wait for deployment to complete
7. Copy the generated URL (e.g., `https://your-app-name.vercel.app`)

### Step 4: Update Backend CORS
1. Go back to your Render dashboard
2. Update the CORS configuration in `auth_backend.py` with your Vercel domain
3. Redeploy the backend

## Testing the Deployment

1. Open your Vercel frontend URL
2. Test the enrollment and authentication features
3. Check the browser console for any CORS errors
4. Verify that the API calls are working correctly

## Environment Variables (Optional)

For better security, you can set environment variables:

### Render (Backend)
- `DATABASE_URL`: Your database connection string
- `SECRET_KEY`: A secret key for your application

### Vercel (Frontend)
- `VITE_API_BASE_URL`: Your backend API URL

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the frontend domain is added to the backend CORS origins
2. **API 404 Errors**: Verify the API routes are correctly configured
3. **Build Failures**: Check that all dependencies are in `requirements.txt` and `package.json`

### Debugging

1. Check Render logs for backend errors
2. Check Vercel logs for frontend build errors
3. Use browser developer tools to debug API calls
4. Verify environment variables are set correctly

## Local Development

To run the application locally:

### Backend
```bash
cd /path/to/your/project
pip install -r requirements.txt
uvicorn auth_backend:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will proxy API calls to `http://localhost:8000` during development.

## Security Considerations

1. Update CORS origins to only include your production domains
2. Consider adding authentication to your API endpoints
3. Use environment variables for sensitive configuration
4. Regularly update dependencies for security patches 