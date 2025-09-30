# 🚀 Production Deployment Guide

## Overview
This guide covers deploying the Kuryecini platform to production using:
- **Frontend**: Vercel (React SPA)
- **Backend**: Render (FastAPI)
- **Database**: MongoDB Atlas (recommended)

## Prerequisites
- GitHub account with repo access
- Vercel account
- Render account  
- MongoDB Atlas account (or other MongoDB hosting)

---

## 🗄️ Database Setup (MongoDB Atlas)

### 1. Create MongoDB Cluster
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create new project: "Kuryecini Production"
3. Build new cluster (free tier works for testing)
4. Choose region closest to your users
5. Create database user with read/write access
6. Add IP addresses to whitelist (0.0.0.0/0 for now)
7. Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/kuryecini`

### 2. Prepare Database
```bash
# Optional: Seed with sample data
# Connect using MongoDB Compass or CLI
# Database name: kuryecini
# Collections: users, businesses, products, orders
```

---

## 🔧 Backend Deployment (Render)

### 1. Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. New → Web Service
3. Connect GitHub account and select repository
4. Configure service:
   - **Name**: `kuryecini-backend`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your production branch)
   - **Root Directory**: `backend`

### 2. Build & Start Commands
```bash
# Build Command:
pip install -r requirements.txt

# Start Command:  
uvicorn server:app --host 0.0.0.0 --port $PORT
```

### 3. Environment Variables
Add these in Render dashboard → Environment:

```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/kuryecini
JWT_SECRET=your-super-secure-random-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENVIRONMENT=production
```

**⚠️ Security Notes:**
- Generate strong JWT_SECRET: `openssl rand -base64 32`
- Never commit secrets to git
- Use different secrets for production

### 4. Deploy & Verify
1. Click "Create Web Service"
2. Wait for build and deployment
3. Test endpoints:
   ```bash
   curl https://your-app.onrender.com/healthz
   # Should return: {"status":"ok"}
   
   curl https://your-app.onrender.com/menus  
   # Should return: [...] (array of menu items)
   ```

---

## 🎨 Frontend Deployment (Vercel)

### 1. Connect Repository
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. New Project → Import Git Repository
3. Select your repository
4. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### 2. Environment Variables
Add in Vercel → Project Settings → Environment Variables:

```
REACT_APP_BACKEND_URL=https://your-backend.onrender.com
```

**Replace** `your-backend.onrender.com` with your actual Render backend URL.

### 3. Deploy & Verify  
1. Click "Deploy"
2. Wait for build and deployment
3. Test the deployment:
   - Visit your Vercel URL
   - Check browser console for errors
   - Test login flow
   - Verify API calls work (Network tab)

---

## 🧪 Post-Deployment Testing

### Health Checks
```bash
# Backend health
curl https://your-backend.onrender.com/healthz

# Frontend load test
curl -I https://your-frontend.vercel.app
```

### Full Integration Test
1. **Browse Restaurants**: Visit frontend, see restaurant list
2. **User Registration**: Create new customer account  
3. **Menu Browsing**: Click restaurant, view menu items
4. **Cart Operations**: Add items, update quantities
5. **Checkout Flow**: Complete order process
6. **Admin Functions**: Login as admin, verify dashboard
7. **Courier App**: Test map functionality, geolocation

### Performance Monitoring
- **Backend**: Monitor in Render dashboard
- **Frontend**: Check Vercel deployment logs
- **Database**: Monitor MongoDB Atlas metrics

---

## 🔧 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Problem**: Frontend can't connect to backend
**Solution**: 
```python
# In backend/server.py, verify CORS includes your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Environment Variables
**Problem**: App crashes with missing env vars
**Solution**:
- Verify all variables are set in deployment platform
- Check variable names match exactly (.env vs deployed)
- Restart services after updating env vars

#### 3. SPA 404 Errors
**Problem**: Direct URLs return 404
**Solution**: `vercel.json` should be configured (already done in this PR)

#### 4. Build Failures
**Problem**: Deployment fails during build
**Solutions**:
```bash
# Clear cache and try locally first
rm -rf node_modules package-lock.json
npm install  
npm run build

# Check for missing dependencies
npm audit fix
```

#### 5. Database Connection
**Problem**: Backend can't connect to MongoDB
**Solutions**:
- Verify connection string format
- Check database user permissions
- Confirm IP whitelist includes Render IPs
- Test connection string locally first

---

## 🔄 Rollback Procedure

### If deployment fails:

#### Immediate Rollback (Vercel)
1. Go to Vercel project → Deployments  
2. Find last working deployment
3. Click "..." → "Promote to Production"

#### Immediate Rollback (Render)
1. Go to Render service → Deploys
2. Find last working deploy
3. Click "Redeploy" on previous version

#### Code Rollback
```bash
# If you need to revert code changes:
git log --oneline -10  # Find last good commit
git revert <commit-hash>
git push origin main
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring
Set up monitoring for:
- Backend health endpoint: `GET /healthz`
- Frontend uptime
- Database connections
- Error rates

### Log Monitoring
- **Render**: Built-in logging dashboard
- **Vercel**: Function logs and analytics  
- **Database**: MongoDB Atlas monitoring

### Regular Maintenance
- **Weekly**: Check error logs and performance
- **Monthly**: Update dependencies (`npm audit`, `pip list --outdated`)
- **Quarterly**: Review and rotate secrets (JWT_SECRET, etc.)

---

## 🔒 Security Checklist

### Production Security
- [ ] Strong JWT_SECRET (32+ characters)
- [ ] CORS configured for specific domains (not "*")
- [ ] HTTPS enforced (automatic on Vercel/Render)
- [ ] Database access restricted to app servers
- [ ] No secrets in git repository
- [ ] Environment variables properly configured
- [ ] Input validation on all API endpoints
- [ ] Rate limiting configured (if needed)

---

**✅ Your Kuryecini platform is now live in production!**

For support, check the main README.md or create an issue in the repository.