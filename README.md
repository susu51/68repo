# 🚀 Kuryecini - Türkiye'nin En Hızlı Teslimat Platformu

<div align="center">

![Kuryecini Logo](https://via.placeholder.com/200x60/f97316/ffffff?text=Kuryecini)

**Modern, scalable food delivery platform for Turkish market**

[![Build Status](https://github.com/kuryecini/kuryecini-platform/workflows/CI/badge.svg)](https://github.com/kuryecini/kuryecini-platform/actions)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018-blue)](https://reactjs.org/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-MongoDB-green)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](./LICENSE)

[🌐 Live Demo](https://kuryecini.vercel.app) • [📖 API Docs](https://api.kuryecini.com/docs) • [🐛 Issues](https://github.com/kuryecini/kuryecini-platform/issues)

</div>

## 🏗️ Architecture

**Modern Full-Stack Platform with Production-Ready Infrastructure**

- **🎨 Frontend**: React 18 + Vite + Tailwind CSS + shadcn/ui
- **⚡ Backend**: FastAPI + MongoDB + JWT Authentication  
- **🗺️ Maps**: Leaflet + OpenStreetMap integration
- **☁️ Deployment**: Vercel (Frontend) + Render (Backend)
- **📱 Mobile**: Progressive Web App (PWA) ready
- **🔒 Security**: httpOnly cookies + CSRF protection

## ⚡ Quick Start

### 🛠️ Prerequisites

```bash
# Required versions
- Node.js 18+ and yarn
- Python 3.10+
- MongoDB 6.0+
```

### 🚀 Local Development

#### Backend Setup
```bash
# 1. Clone and navigate
git clone https://github.com/kuryecini/kuryecini-platform.git
cd kuryecini-platform/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URL

# 4. Start server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

✅ **Backend Ready**: http://localhost:8001
- 🏥 Health: `/healthz`
- 📚 API Docs: `/docs` 
- 🔍 Interactive: `/redoc`

#### Frontend Setup
```bash
# 1. Navigate to frontend
cd ../frontend

# 2. Install dependencies (using yarn)
yarn install

# 3. Configure environment  
cp .env.example .env
# Edit REACT_APP_BACKEND_URL=http://localhost:8001

# 4. Start development server
yarn start
```

✅ **Frontend Ready**: http://localhost:3000

## 🚀 Production Deployment

### 🔧 Prerequisites for Production

1. **MongoDB Atlas** account and connection string
2. **Render** account for backend deployment  
3. **Vercel** account for frontend deployment
4. **Domain** (optional) for custom URLs

### 📦 Backend Deployment (Render)

#### Step 1: Create Web Service on Render

1. Connect GitHub repository to [Render](https://render.com)
2. Create new **Web Service**
3. Configure deployment:

```yaml
# Render Configuration
Repository: your-github-repo
Branch: main  
Root Directory: backend
Runtime: Python 3.10

# Build Settings
Build Command: pip install -r requirements.txt
Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
```

#### Step 2: Environment Variables

```bash
# Required Environment Variables
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/kuryecini_db
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://kuryecini.com
```

#### Step 3: Verify Deployment

```bash
# Test endpoints after deployment
curl https://your-backend.onrender.com/healthz
curl https://your-backend.onrender.com/api/menus/public
```

### 🌐 Frontend Deployment (Vercel)

#### Step 1: Deploy to Vercel

1. Connect GitHub repository to [Vercel](https://vercel.com)
2. Import project with these settings:

```yaml
# Vercel Configuration  
Framework Preset: Create React App
Root Directory: frontend
Build Command: yarn build
Output Directory: build
Install Command: yarn install
```

#### Step 2: Environment Variables

```bash
# Production Environment Variables
REACT_APP_BACKEND_URL=https://your-backend.onrender.com
```

#### Step 3: Verify SPA Routing

The `frontend/vercel.json` file handles SPA routing:

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## 🏭 Production Environment Files

### Create Production Environment Files

#### Backend `.env` (Production)
```bash
# backend/.env
MONGO_URL="mongodb+srv://username:password@cluster.mongodb.net/kuryecini_production"
JWT_SECRET_KEY="your-production-jwt-secret-very-long-and-secure"
CORS_ORIGINS="https://kuryecini.vercel.app,https://kuryecini.com"
```

#### Frontend `.env` (Production)
```bash
# frontend/.env
REACT_APP_BACKEND_URL="https://kuryecini-api.onrender.com"
```

## 🔧 CI/CD Pipeline

### GitHub Actions Workflow

The repository includes automated CI/CD with comprehensive testing:

```yaml
# .github/workflows/ci.yml
- Frontend build and validation
- Backend API testing  
- Integration testing
- Deployment artifacts
```

### Running Tests Locally

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests  
cd frontend
yarn test

# E2E tests
yarn test:e2e
```

## Features

### Customer App
- Browse restaurants and menus
- Add items to cart with quantities
- Address management (81 Turkish cities)
- Order tracking with live map
- Rating and reviews

### Restaurant Dashboard
- Menu management (add/edit/delete items)
- Order processing and status updates
- Analytics dashboard
- Business profile management

### Courier App
- Interactive map with Leaflet
- Available orders nearby
- Route optimization
- Earnings tracking
- Real-time location sharing

### Admin Panel
- User management
- Restaurant approval (KYC)
- Order monitoring
- Platform analytics

## API Endpoints

### Health Check
```
GET /healthz
Response: {"status": "ok"}
```

### Menus
```
GET /menus
Response: [
  {
    "id": "string",
    "title": "string", 
    "price": number,
    "imageUrl": "string",
    "category": "string"
  }
]
```

## Testing

Run the end-to-end tests:
```bash
npm run test:e2e
```

## Common Issues

### CORS Errors
- Ensure backend CORS is configured for your frontend domain
- Check REACT_APP_BACKEND_URL is correct

### SPA 404 on Refresh
- Vercel: `vercel.json` rewrites are configured
- Netlify: `_redirects` file in `public/` folder

### Map Not Loading
- Check Leaflet CSS import: `import 'leaflet/dist/leaflet.css'`
- Map container needs fixed height (e.g., `height: 100vh`)
- Handle geolocation permissions gracefully

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Contributing

1. Create feature branch: `git checkout -b feat/your-feature`
2. Make changes and test locally
3. Run linting: `npm run lint`
4. Open PR to `main`

## Rollback Plan

If deployment fails:
1. Revert to previous commit: `git revert HEAD`
2. Redeploy previous version
3. Check environment variables
4. Monitor error logs