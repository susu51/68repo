# Kuryecini - Food Delivery Platform

A full-stack food delivery platform with courier tracking, restaurant management, and customer ordering.

## Architecture

- **Frontend**: React (Create React App) + Tailwind CSS
- **Backend**: FastAPI + MongoDB
- **Maps**: Leaflet + OpenStreetMap
- **Authentication**: JWT tokens

## Local Development

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+
- MongoDB (local or Docker)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MongoDB URL and JWT secret
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000
- Health check: http://localhost:8000/healthz
- API docs: http://localhost:8000/docs

### Frontend Setup
```bash
cd frontend
npm install  # or yarn install
cp .env.example .env
# Edit .env with backend URL (REACT_APP_BACKEND_URL)
npm start  # or yarn start
```

Frontend will be available at http://localhost:3000

## Production Deployment

### Backend (Render)
1. Connect your GitHub repo to Render
2. Create a new Web Service
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   - `MONGO_URL`: Your MongoDB connection string
   - `JWT_SECRET`: Strong random secret
   - `ENVIRONMENT`: `production`

### Frontend (Vercel)
1. Connect your GitHub repo to Vercel
2. Framework Preset: Create React App
3. Build Command: `npm run build`
4. Output Directory: `build`
5. Root Directory: `frontend`
6. Environment Variables:
   - `REACT_APP_BACKEND_URL`: Your Render backend URL

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