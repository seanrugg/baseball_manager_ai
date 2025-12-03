# 🚀 Start Here: Frontend Deployment to Plesk

Your React frontend is ready to deploy to your Plesk VPS. This guide walks you through the process using Plesk's web interface.

## What You're Deploying

A complete React application with:
- User authentication (login/signup)
- User dashboard with game predictions
- Admin dashboard with analytics
- Profile management
- Mobile-responsive design
- Production-optimized build

## Prerequisites

✅ Node.js 16+ installed locally
✅ Access to your Plesk panel
✅ Your domain name (e.g., yourdomain.com)
✅ Backend API deployed (or being deployed separately)

## Quick Overview

| Step | Time | Action |
|------|------|--------|
| 1 | 5 min | Build locally |
| 2 | 2 min | Create domain in Plesk |
| 3 | 5 min | Upload files via Plesk File Manager |
| 4 | 3 min | Configure Nginx |
| 5 | 5 min | Install SSL certificate |
| 6 | 2 min | Test |

**Total: ~25 minutes**

## Step 1: Build Locally

On your local machine:

```bash
cd frontend
npm install
npm run build
```

This creates a `dist/` folder with all static files ready to upload.

## Step 2: Create Domain in Plesk

1. Open Plesk panel: `https://your-plesk-panel.com:8443`
2. Go to **Subscriptions** (or **Domains**)
3. Click **Add Subscription**
4. Fill in:
   - **Domain name**: `yourdomain.com`
   - **Login**: Create admin username
   - **Password**: Create strong password
5. Click **OK**

Wait for domain to be created (~2 minutes).

## Step 3: Upload Frontend Files

1. In Plesk, select your domain (`yourdomain.com`)
2. Click **File Manager**
3. Navigate to `httpdocs` folder
4. Delete any existing files
5. Click **Upload**
6. Select all files from your local `frontend/dist/` folder
7. Wait for upload to complete

## Step 4: Configure Nginx (Critical!)

This step is essential for React Router to work properly.

1. In Plesk, select your domain
2. Go to **Web Hosting** → **Nginx Settings** (or **Apache/Nginx Settings**)
3. Find the "Custom configuration" section
4. Paste this configuration:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}

location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

5. Click **OK** to apply

## Step 5: Install SSL Certificate

1. In Plesk, select your domain
2. Go to **SSL/TLS Certificates**
3. Click **Install Certificate**
4. Select **Let's Encrypt (Free)**
5. Check both domain and www.domain
6. Click **Install**

Wait a few seconds for certificate to be installed.

## Step 6: Enable HTTPS Redirect

1. In Plesk, select your domain
2. Go to **Security** section
3. Find "Always use HTTPS" option
4. Enable it
5. Click **OK**

## Step 7: Test Your Frontend

Open in browser: `https://yourdomain.com`

You should see the login page. ✅

### Test These:

- [ ] Page loads (no 404 errors)
- [ ] Can see login form
- [ ] Click "Sign Up" works
- [ ] Can fill signup form
- [ ] Submit signup (will connect to backend API)

If you see blank page or errors, check:
1. Browser console (F12)
2. Check that all files uploaded to httpdocs
3. Verify Nginx config was applied

## Connecting to Your Backend API

The frontend expects your backend at a specific URL.

**Update API URL:**

1. In Plesk File Manager, find `index.html` in httpdocs
2. Look for `VITE_API_URL` - it should be set to your backend API URL
3. If needed, edit the file to set correct URL

Or rebuild locally with correct API URL:

```bash
cd frontend
# Edit .env.production
VITE_API_URL=https://api.yourdomain.com
# or wherever your backend is

npm run build
# Upload new dist/ files
```

## Common Issues

### "Cannot GET /" on page refresh

**Problem**: Clicking links works, but F5 refresh shows 404

**Solution**: The Nginx config wasn't applied properly. Re-apply configuration from Step 4.

### Blank page or JS errors

**Problem**: Page is blank or shows JavaScript errors

**Solution**:
1. Check browser console (F12 → Console tab)
2. Verify all files in `dist/` were uploaded
3. Clear browser cache (Ctrl+Shift+Delete)
4. Rebuild and re-upload

### Login doesn't work

**Problem**: Can't login, API errors

**Solution**:
1. Check browser Network tab (F12 → Network)
2. Look for API requests and check response
3. Verify backend is running and accessible
4. Check `VITE_API_URL` is correct

### Files not uploading

**Problem**: Upload fails or hangs

**Solution**:
1. Try uploading files in batches (smaller groups)
2. Check file permissions
3. Verify you have storage space
4. Try different browser

## Next Steps

### If Everything Works:

1. Create a test user (signup/login)
2. Explore dashboard and pages
3. Test on mobile (responsive design)
4. Check all navigation links
5. Verify admin pages (if applicable)

### If Something Doesn't Work:

1. Check [PLESK_REACT_DEPLOYMENT.md](./PLESK_REACT_DEPLOYMENT.md) for detailed troubleshooting
2. Review [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) for configuration help
3. Check Plesk logs: **Domains** → **Logs**

## Updating Your Frontend

When you make changes and want to update:

```bash
cd frontend
npm run build
# Upload new dist/ files to Plesk (via File Manager)
```

## Getting Help

**For deployment issues:**
- Check [PLESK_REACT_DEPLOYMENT.md](./PLESK_REACT_DEPLOYMENT.md)
- Review troubleshooting section below

**For backend integration issues:**
- Ensure backend API is running
- Check API URL is correct
- Verify CORS is enabled on backend

**For browser console errors:**
- Check network tab for failed requests
- Look at API responses
- Check browser console for JavaScript errors

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| 404 on page refresh | Re-apply Nginx config (Step 4) |
| Blank page | Check F12 console, verify files uploaded |
| Login fails | Check API URL, verify backend running |
| Styles not loading | Verify CSS files in dist/, clear cache |
| Mobile not responsive | Check viewport meta tag in index.html |

## Quick Reference URLs

- **Frontend**: `https://yourdomain.com`
- **Plesk Panel**: `https://your-plesk-panel.com:8443`
- **Backend API**: `https://api.yourdomain.com` (if separate)

## Files Reference

| File | Purpose |
|------|---------|
| `frontend/dist/` | Files to upload to Plesk |
| `frontend/.env.production` | Production environment config |
| `frontend/package.json` | Dependencies |
| `frontend/vite.config.js` | Build configuration |

## Summary

Your React frontend is now live on Plesk! 🎉

- ✅ Modern responsive design
- ✅ User authentication
- ✅ Admin dashboard
- ✅ Mobile-friendly
- ✅ Production-ready

## Next Steps After Deployment

1. **Team setup**: Invite team members and create accounts
2. **Testing**: Verify all features work on different devices
3. **Monitoring**: Set up backups and monitoring
4. **Optimization**: Monitor performance and make improvements
5. **Integration**: Connect data sources and configure predictions

---

**Questions?** See detailed guides:
- [PLESK_REACT_DEPLOYMENT.md](./PLESK_REACT_DEPLOYMENT.md) - Complete step-by-step guide
- [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) - Configuration and troubleshooting
