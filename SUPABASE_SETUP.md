# Supabase Setup Guide (Free Cloud Database)

This guide will help you set up Supabase as a free PostgreSQL database for your keystroke dynamics authentication system.

## Step 1: Create Supabase Account

1. **Go to Supabase**: https://supabase.com/
2. **Click "Start your project"**
3. **Sign up with GitHub** (recommended)
4. **Create a new project**

## Step 2: Set Up Database

1. **Choose a project name**: `keystroke-auth-db`
2. **Choose a database password** (save this!)
3. **Choose a region** (closest to your users)
4. **Click "Create new project"**
5. **Wait for setup to complete** (2-3 minutes)

## Step 3: Get Database Connection Details

1. **Go to Settings > Database**
2. **Copy the connection string**:
   ```
   postgresql://postgres:[password]@[host]:[port]/postgres
   ```
3. **Save this for later**

## Step 4: Create Tables (Optional - Auto-created)

The tables will be created automatically when you first run the application, but you can also create them manually:

1. **Go to SQL Editor**
2. **Run this SQL**:

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Samples table
CREATE TABLE IF NOT EXISTS samples (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    features_json TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    model_data_base64 TEXT NOT NULL,
    model_type VARCHAR NOT NULL,
    feature_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Step 5: Set Environment Variables

### For Render Deployment:

1. **Go to your Render dashboard**
2. **Select your backend service**
3. **Go to "Environment" tab**
4. **Add this environment variable**:

```
DATABASE_URL = postgresql://postgres:[password]@[host]:[port]/postgres
```

Replace `[password]`, `[host]`, and `[port]` with your actual Supabase values.

## Step 6: Update Render Configuration

Your `render.yaml` should look like this:

```yaml
services:
  - type: web
    name: keystroke-auth-backend
    env: python
    plan: free
    buildCommand: chmod +x build.sh && ./build.sh
    startCommand: uvicorn auth_backend:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12
      - key: DATABASE_URL
        value: postgresql://postgres:[password]@[host]:[port]/postgres
```

## Step 7: Deploy and Test

1. **Commit and push your changes**:
   ```bash
   git add .
   git commit -m "Add Supabase database support"
   git push origin main
   ```

2. **Deploy on Render**
3. **Test the API endpoints**

## Alternative: Use SQLite for Development

For local development, you can use SQLite:

```bash
# Set environment variable for local development
export DATABASE_URL=sqlite:///./auth.db

# Run the application
uvicorn auth_backend:app --reload
```

## Benefits of Supabase

- **Free tier**: 500MB database, 50MB file storage
- **PostgreSQL**: Full SQL database
- **Real-time**: Built-in real-time subscriptions
- **Auth**: Built-in authentication (if needed later)
- **API**: Auto-generated REST API
- **Dashboard**: Web interface to manage data

## Troubleshooting

### Common Issues:

1. **"Connection refused"**
   - Check if the DATABASE_URL is correct
   - Verify Supabase project is active

2. **"Table doesn't exist"**
   - Tables are created automatically on first run
   - Or run the SQL manually in Supabase SQL Editor

3. **"Permission denied"**
   - Check if the password is correct
   - Verify the connection string format

### Security Notes:

- Keep your database password secure
- Use environment variables for sensitive data
- Supabase provides SSL by default
- Consider using connection pooling for production

## Local Development

Create a `.env` file for local development:

```
DATABASE_URL=sqlite:///./auth.db
```

Then run:
```bash
uvicorn auth_backend:app --reload
```

## Production Considerations

For production:
1. **Use connection pooling**
2. **Set up proper backups**
3. **Monitor database performance**
4. **Consider upgrading to paid plan** if needed 