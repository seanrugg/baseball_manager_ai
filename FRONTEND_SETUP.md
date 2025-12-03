# Frontend Setup & Configuration

Complete guide for local setup, configuration, and troubleshooting of the React frontend.

## Quick Start

### Prerequisites

- Node.js 16 or higher
- npm or yarn
- Git (optional)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000` with hot reload.

### Production Build

```bash
npm run build
```

Creates optimized `dist/` folder for deployment.

---

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.jsx       # Main layout wrapper
│   │   ├── Navbar.jsx       # Navigation bar
│   │   └── ProtectedRoute.jsx
│   ├── pages/              # Page components (routes)
│   │   ├── LoginPage.jsx
│   │   ├── SignupPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── PredictionsPage.jsx
│   │   ├── ProfilePage.jsx
│   │   └── admin/
│   │       ├── UsersPage.jsx
│   │       └── AnalyticsPage.jsx
│   ├── stores/             # State management
│   │   └── authStore.js    # User/auth state
│   ├── api/                # API client
│   │   ├── client.js       # Axios configuration
│   │   ├── auth.js         # Auth endpoints
│   │   ├── dashboard.js    # Dashboard endpoints
│   │   └── admin.js        # Admin endpoints
│   ├── utils/              # Utility functions
│   │   └── helpers.js      # Date, format utils
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html              # HTML template
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS config
├── postcss.config.js       # PostCSS config
├── package.json            # Dependencies
├── .env.development        # Dev environment
├── .env.production         # Production environment
└── README.md              # Frontend docs
```

---

## Configuration

### Environment Variables

Two environment files control configuration:

#### Development (.env.development)

Used when running `npm run dev`:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Baseball Manager AI
```

**For local development:**
- `VITE_API_URL`: Should point to your local backend (usually `http://localhost:8000`)

#### Production (.env.production)

Used when running `npm run build`:

```env
VITE_API_URL=https://api.yourdomain.com
VITE_APP_NAME=Baseball Manager AI
```

**For production deployment:**
- `VITE_API_URL`: Point to your backend API on VPS
- Replace `api.yourdomain.com` with your actual backend URL

### Changing API URL

**For Development:**

1. Edit `frontend/.env.development`
2. Update `VITE_API_URL` to point to your backend
3. Restart dev server: `npm run dev`

**For Production:**

1. Edit `frontend/.env.production`
2. Update `VITE_API_URL` to your backend URL
3. Run build: `npm run build`
4. Upload new `dist/` to Plesk

---

## Development

### Run Development Server

```bash
cd frontend
npm run dev
```

Features:
- Hot module replacement (code changes instantly appear)
- Opens at `http://localhost:3000`
- API proxy configured (if needed)
- Source maps for debugging

### Code Organization

**Components** (`src/components/`):
- Reusable UI components
- Layout wrapper
- Protected route guard

**Pages** (`src/pages/`):
- Full page components
- Each represents a route
- Can include page-specific state

**Stores** (`src/stores/`):
- Global state with Zustand
- Auth store with user data
- Token management

**API** (`src/api/`):
- Axios client configuration
- API endpoint modules
- Error handling

### Debugging

**Browser DevTools (F12):**

1. **Console tab:**
   - Check for JavaScript errors
   - Look for network/API errors
   - See logs from your code

2. **Network tab:**
   - See API requests/responses
   - Check request headers (auth token)
   - Verify API URL

3. **Application tab:**
   - Check localStorage (auth token)
   - Verify cookies

**React DevTools:**

1. Install browser extension: "React Developer Tools"
2. In F12, new tab "Components" appears
3. Inspect component state and props

---

## Building for Production

### Build Process

```bash
cd frontend
npm run build
```

This:
1. Compiles React JSX to JavaScript
2. Minifies CSS and JavaScript
3. Bundles assets
4. Optimizes for production
5. Creates `dist/` folder

### Build Output

```
dist/
├── index.html          (main HTML file)
├── assets/
│   ├── index-xxx.js    (main JavaScript)
│   ├── index-xxx.css   (styles)
│   └── [vendor code]
└── [static files]
```

**Size expectations:**
- Main JS: 50-100KB
- CSS: 10-20KB
- Total gzipped: ~150KB

### Preview Production Build

To test the production build locally:

```bash
npm run preview
```

Opens at `http://localhost:4173` - shows how production will look.

---

## Technology Stack Details

### React 18

Modern React with:
- Hooks for state management
- Functional components
- Concurrent features

### Vite 5

Fast build tool with:
- Instant dev server startup
- Hot module replacement
- Optimized production builds
- ~10x faster than Webpack

### Tailwind CSS

Utility-first CSS framework:
- No custom CSS needed
- Responsive design built-in
- Easy customization via `tailwind.config.js`

### React Router v6

Client-side routing:
- Fast navigation between pages
- Protected routes
- Nested routes
- Query parameters

### Zustand

Lightweight state management:
- Simple API
- Less boilerplate than Redux
- Good for auth state
- Persists to localStorage

### Axios

HTTP client:
- Request/response interceptors
- Automatic JWT header injection
- Better error handling than fetch
- Built-in timeout

---

## Common Tasks

### Add a New Page

1. Create component in `src/pages/NewPage.jsx`:

```jsx
export function NewPage() {
  return (
    <div>
      <h1>New Page</h1>
    </div>
  )
}
```

2. Add route in `src/App.jsx`:

```jsx
import { NewPage } from './pages/NewPage'

<Route path="/newpage" element={
  <ProtectedRoute>
    <Layout>
      <NewPage />
    </Layout>
  </ProtectedRoute>
} />
```

3. Add nav link in `src/components/Navbar.jsx`

### Add a New Component

1. Create in `src/components/MyComponent.jsx`:

```jsx
export function MyComponent({ data }) {
  return <div>{data}</div>
}
```

2. Import and use in pages:

```jsx
import { MyComponent } from '../components/MyComponent'

<MyComponent data="example" />
```

### Call an API

1. Add method to API module (`src/api/dashboard.js`):

```js
export const dashboardAPI = {
  getData: async () => {
    const { data } = await client.get('/dashboard/data')
    return data
  }
}
```

2. Use in component:

```jsx
import { dashboardAPI } from '../api/dashboard'
import { useEffect, useState } from 'react'

function MyPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    dashboardAPI.getData().then(setData)
  }, [])

  return <div>{data}</div>
}
```

### Access User Data

From anywhere in app:

```jsx
import { useAuthStore } from '../stores/authStore'

function MyComponent() {
  const { user, role, isAdmin } = useAuthStore()

  return (
    <div>
      {user?.email}
      {isAdmin && <AdminFeature />}
    </div>
  )
}
```

### Logout User

```jsx
import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router-dom'

function LogoutButton() {
  const { logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return <button onClick={handleLogout}>Logout</button>
}
```

---

## Troubleshooting

### "npm: command not found"

**Problem:** Node.js not installed

**Solution:**
1. Download from nodejs.org
2. Install Node.js
3. Verify: `node --version` and `npm --version`

### "Cannot find module" error

**Problem:** Dependencies not installed

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Port 3000 Already in Use

**Problem:** Another app using port 3000

**Solution:**
```bash
# Linux/Mac: Kill process
lsof -ti:3000 | xargs kill -9

# Windows: Stop and restart Node

# Or use different port:
npm run dev -- --port 3001
```

### API Requests Failing

**Problem:** Can't connect to backend

**Steps to debug:**
1. Check `VITE_API_URL` in `.env.development`
2. Verify backend is running
3. Check browser Network tab (F12)
4. Look for error details
5. Check backend logs

**Common causes:**
- Wrong API URL
- Backend not running
- CORS not enabled on backend
- Firewall blocking requests

### Blank Page After Build

**Problem:** `npm run build` succeeds but page blank after deploy

**Steps to check:**
1. Check browser console (F12)
2. Look for JavaScript errors
3. Check Network tab for failed requests
4. Verify all files uploaded
5. Clear browser cache

### Hot Reload Not Working

**Problem:** Changes to code don't refresh automatically

**Solution:**
1. Restart dev server: `Ctrl+C` then `npm run dev`
2. Check that you're editing correct file
3. Check for syntax errors
4. Try clearing browser cache

### Styles Not Applying

**Problem:** Tailwind CSS classes not working

**Cause:** Usually build issue

**Solution:**
1. Verify `tailwind.config.js` is correct
2. Restart dev server
3. Clear browser cache
4. Rebuild: `npm run build`

### Login Not Working

**Problem:** Can't login, API error

**Debug steps:**
1. Check F12 Console for errors
2. Check Network tab for API response
3. Verify `VITE_API_URL` is correct
4. Test backend separately (e.g., with curl/Postman)
5. Check CORS headers on backend

### Mobile View Issues

**Problem:** Doesn't look right on mobile

**Debug:**
1. Open browser DevTools F12
2. Click device icon (toggle mobile view)
3. Test different screen sizes
4. Check that images/text are readable
5. Verify buttons are clickable

---

## Performance Tips

### 1. Code Splitting

Already configured in Vite. Routes are automatically split.

### 2. Image Optimization

Use optimized images:
```jsx
// Good: small, optimized image
<img src="/images/small.webp" alt="description" />

// Avoid: large unoptimized image
<img src="/images/large-original.jpg" alt="description" />
```

### 3. Lazy Loading Components

```jsx
import { lazy, Suspense } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

function MyPage() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  )
}
```

### 4. Memoize Components

```jsx
import { memo } from 'react'

const MyComponent = memo(function MyComponent({ data }) {
  return <div>{data}</div>
})
```

### 5. Cache API Responses

```jsx
const cache = {}

async function getCachedData(key) {
  if (cache[key]) return cache[key]
  const data = await api.get(key)
  cache[key] = data
  return data
}
```

---

## Deployment Preparation

### Before Building for Production

1. **Update API URL:**
   - Edit `.env.production`
   - Set `VITE_API_URL` to your backend

2. **Test locally:**
   - Run `npm run preview`
   - Test all pages
   - Verify mobile responsive

3. **Build:**
   ```bash
   npm run build
   ```

4. **Verify dist folder:**
   - Check `dist/` exists
   - Check `index.html` is present
   - Check `assets/` folder has JS/CSS

5. **Upload to Plesk:**
   - See PLESK_REACT_DEPLOYMENT.md

---

## File Reference

| File | Purpose |
|------|---------|
| `src/App.jsx` | Main app, routes configuration |
| `src/main.jsx` | Entry point, mounts React |
| `src/index.css` | Global styles |
| `vite.config.js` | Vite build configuration |
| `tailwind.config.js` | Tailwind theme customization |
| `package.json` | Dependencies and scripts |
| `.env.development` | Dev environment variables |
| `.env.production` | Production environment variables |
| `index.html` | HTML template |

---

## Scripts Available

```bash
npm run dev       # Start dev server
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Lint code (if configured)
```

---

## Next Steps

1. **Local Testing:**
   - `npm run dev`
   - Test all pages
   - Test mobile view

2. **Production Build:**
   - Update `.env.production`
   - `npm run build`
   - Verify `dist/` folder

3. **Deploy to Plesk:**
   - Follow PLESK_REACT_DEPLOYMENT.md
   - Upload `dist/` files
   - Configure Nginx
   - Install SSL

4. **Go Live:**
   - Test production deployment
   - Verify all features work
   - Invite users

---

## Getting Help

**For specific errors:**
1. Check troubleshooting section above
2. Search error message in browser console
3. Check backend logs for API errors

**For feature questions:**
- See FRONTEND_README.md

**For Plesk deployment:**
- See PLESK_REACT_DEPLOYMENT.md

---

**Your frontend is ready to deploy!** 🚀
