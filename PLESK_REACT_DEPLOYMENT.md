# Complete Plesk Deployment Guide for React Frontend

Detailed step-by-step instructions for deploying your React frontend to Plesk using the web interface.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Build Preparation](#build-preparation)
3. [Create Domain in Plesk](#create-domain-in-plesk)
4. [Upload Files](#upload-files)
5. [Configure Nginx](#configure-nginx)
6. [Install SSL Certificate](#install-ssl-certificate)
7. [Environment Configuration](#environment-configuration)
8. [Testing & Verification](#testing--verification)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

---

## Prerequisites

- ✅ Node.js 16 or higher installed locally
- ✅ Access to Plesk panel (username/password)
- ✅ Domain name purchased and pointed to your VPS
- ✅ Backend API deployed (or deployment planned separately)
- ✅ Modern web browser (Chrome, Firefox, Safari, Edge)

## Build Preparation

### 1.1 Verify Environment Configuration

Before building, ensure your environment is configured:

**Edit `frontend/.env.production`:**

```env
VITE_API_URL=https://api.yourdomain.com
VITE_APP_NAME=Baseball Manager AI
```

Replace:
- `yourdomain.com` with your actual domain
- `api.yourdomain.com` with your backend API URL

### 1.2 Build the Frontend

On your **local machine**:

```bash
cd frontend
npm install
npm run build
```

This creates a `dist/` folder with all static files.

### 1.3 Verify Build

Check that `dist/` folder contains:

```
dist/
├── index.html
├── assets/
│   ├── index-xxx.js (JavaScript bundle)
│   ├── index-xxx.css (Styles)
│   └── [other assets]
└── [other static files]
```

---

## Create Domain in Plesk

### 2.1 Access Plesk Panel

1. Open browser and go to: `https://your-server-ip:8443` or `https://your-plesk-domain.com:8443`
2. Login with your Plesk credentials
3. You should see the Plesk Dashboard

### 2.2 Navigate to Subscriptions

Method A (New Plesk):
- Left sidebar → **Subscriptions**

Method B (Classic Plesk):
- Top menu → **Subscriptions** or **Domains**

### 2.3 Create New Subscription

1. Click **Add Subscription** (or **Add Domain**)
2. A form appears with these fields:

**Domain Information:**
- **Domain name**: `yourdomain.com` (use your actual domain)
- **IPv4 address**: Select from dropdown (usually default is fine)
- **IPv6 address**: Leave as default

**Administrator:**
- **Login**: Create username (e.g., `admin_baseball`)
- **Password**: Create strong password
- **Email**: Your email address

3. Scroll down and click **OK** or **Create**

Wait 1-2 minutes for Plesk to set up the domain.

### 2.4 Verify Domain Creation

1. You should see your domain in the subscriptions list
2. Status should show as "Active" (green check)
3. Click on your domain to open its management panel

---

## Upload Files

### 3.1 Access File Manager

1. In Plesk, select your domain
2. Look for **File Manager** option (usually in left sidebar or top menu)
3. Click **File Manager**

A new window or panel opens with folder structure.

### 3.2 Navigate to Document Root

1. In File Manager, you should see folders:
   - `httpdocs` (this is where public files go) ← **USE THIS**
   - `httpsdocs`
   - `private_html`

2. Double-click **httpdocs** to open it

### 3.3 Delete Existing Files (if any)

If there are existing files in httpdocs:

1. Select all files: `Ctrl+A`
2. Right-click → **Delete**
3. Confirm deletion
4. Wait for deletion to complete

### 3.4 Upload Frontend Files

**Option A: Upload via Browser (Recommended)**

1. Click **Upload** button in File Manager
2. Select all files from your local `frontend/dist/` folder:
   - Click on `dist` folder
   - Select all files inside (`Ctrl+A`)
   - Click **Open**
3. File Manager shows upload progress
4. Wait for "Upload complete" message

**Option B: Upload Individual Files**

If uploading all at once fails:

1. Click **Upload**
2. Select files in batches (e.g., 10-20 at a time)
3. Wait for each batch to complete before uploading next

**Option C: Create Folders First (if needed)**

If dist has asset folders:

1. In File Manager, right-click → **Create Folder**
2. Name it `assets`
3. Double-click to enter
4. Upload files into it

### 3.5 Verify Upload

1. In File Manager, confirm you see:
   - `index.html` (main HTML file)
   - `assets/` folder (containing JS/CSS)
   - Any other static files

2. File count should match your `dist/` folder

---

## Configure Nginx

This is **critical** for React Router to work properly!

### 4.1 Access Web Hosting Settings

1. In Plesk, select your domain
2. Look for **Web Hosting** or **Hosting** section
3. Click **Web Hosting**

You should see hosting details and settings.

### 4.2 Find Nginx Configuration

Look for one of these options:

- **Nginx Settings** (newer Plesk)
- **Apache & Nginx Settings** (combined)
- **Web Server Configuration**

Click on it.

### 4.3 Add Custom Configuration

You should see a section for custom configuration. Look for:

- "Additional nginx directives"
- "Custom configuration"
- "nginx configuration" field

In this field, paste this configuration:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}

location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**What this does:**
- `try_files $uri $uri/ /index.html;` - Routes all requests to index.html (React Router requirement)
- The second block caches static assets for 1 year (performance)

### 4.4 Apply Configuration

1. Scroll to bottom of the page
2. Click **OK** or **Apply**

Nginx configuration is now updated.

### 4.5 Verify Configuration Applied

After clicking OK:

1. You should see a success message
2. Domain page reloads
3. Configuration is now active

---

## Install SSL Certificate

### 5.1 Access SSL Settings

1. In Plesk, select your domain
2. Look for **SSL/TLS Certificates** or **SSL** option
3. Click it

### 5.2 Install Let's Encrypt Certificate

1. Click **Install Certificate** (or **Add SSL Certificate**)
2. A dialog appears with certificate options
3. Select **Let's Encrypt (Free)**
4. Check domains:
   - ☑ `yourdomain.com`
   - ☑ `www.yourdomain.com`
5. Click **Install**

Plesk requests certificate from Let's Encrypt (~30 seconds).

You should see success message.

### 5.3 Enable HTTPS Redirect

1. Still in SSL settings (or go to **Security**)
2. Look for option:
   - "Redirect all requests to secure connection"
   - "Always use HTTPS"
   - "Force secure connection"

3. Enable this option (check the box)
4. Click **OK** or **Apply**

Now all HTTP traffic redirects to HTTPS.

---

## Environment Configuration

### 6.1 Verify API URL in Frontend

Your frontend needs to know where your backend API is.

**The API URL is set during build:**

```bash
cd frontend
# Edit .env.production with correct API URL
VITE_API_URL=https://api.yourdomain.com

npm run build
```

Then upload the new `dist/` files.

### 6.2 Confirm Settings in Plesk File Manager

To verify the built files have correct settings:

1. In File Manager, right-click on `index.html`
2. Click **Edit** or **View Source**
3. Look for references to your API URL
4. Should be embedded in the JavaScript

---

## Testing & Verification

### 7.1 Test Frontend Load

1. Open browser: `https://yourdomain.com`
2. Should load the login page
3. Check for:
   - ✅ Page loads quickly
   - ✅ No 404 errors
   - ✅ Styling looks correct
   - ✅ Logo/images display

### 7.2 Test Navigation

1. Open browser **Console** (F12 → Console tab)
2. Test these actions:
   - ✅ Click **Sign Up** - navigation works
   - ✅ Click **Login** link - navigation works
   - ✅ Page refresh on `/signup` - still works (not 404)
   - ✅ No JavaScript errors in console

### 7.3 Test Forms

1. Try signing up with test email
2. If backend is ready:
   - ✅ Signup completes
   - ✅ Can login with credentials
   - ✅ See dashboard

If backend is not ready yet:
- ✅ Form appears and accepts input
- ✅ Submit button works (may show API error)

### 7.4 Test Mobile View

1. Press F12 to open Developer Tools
2. Click device icon (mobile view)
3. Test:
   - ✅ Layout is responsive
   - ✅ Navigation menu collapses
   - ✅ Forms are usable on mobile
   - ✅ All content visible

### 7.5 Check Performance

1. In browser F12 → **Network** tab
2. Reload page
3. Check:
   - ✅ Load time < 3 seconds
   - ✅ Total file size reasonable
   - ✅ No failed requests (red)

---

## Troubleshooting

### Issue: "Cannot GET /" on Page Refresh

**Symptom:**
- Clicking links works fine
- But pressing F5 (page refresh) shows 404 error

**Cause:**
- Nginx configuration not applied properly

**Solution:**
1. Go back to **Web Hosting** → **Nginx Settings**
2. Find the configuration section
3. Clear it and paste again:
   ```nginx
   location / {
       try_files $uri $uri/ /index.html;
   }
   ```
4. Click **OK**
5. Test by going to `/signup` directly in URL bar (should not 404)

### Issue: Blank Page or JavaScript Errors

**Symptom:**
- Page loads but is blank
- Console shows JavaScript errors

**Cause:**
- Files not fully uploaded
- Build has errors
- Incorrect API URL

**Solution:**
1. Check browser **Console** (F12 → Console tab)
2. Look for error messages
3. Common errors:
   - `Failed to fetch from API` → Check API URL
   - `Cannot find module` → Rebuild locally
   - `index.html not found` → Re-upload files

**If still having issues:**
1. Delete all files in httpdocs (in Plesk File Manager)
2. Rebuild locally: `npm run build`
3. Re-upload all dist files
4. Clear browser cache: `Ctrl+Shift+Delete`

### Issue: Login Doesn't Work

**Symptom:**
- Can access login page
- Cannot login, shows error

**Cause:**
- Backend API not running
- API URL wrong
- CORS configuration issue

**Solution:**
1. Check browser **Network** tab (F12 → Network)
2. Try logging in
3. Look for API request in Network tab
4. Click on request, check response
5. If error from API:
   - Verify backend is running
   - Check API URL is correct
   - Ensure CORS enabled on backend

### Issue: Styles Not Applied

**Symptom:**
- Page loads but styling looks wrong
- CSS not loading

**Cause:**
- CSS files not uploaded
- Cache issue
- File permissions

**Solution:**
1. Check in File Manager that `assets/` folder exists
2. Check it contains CSS files
3. Clear browser cache: `Ctrl+Shift+Delete`
4. In browser Network tab (F12), check if CSS loads
5. Re-upload if needed

### Issue: Static Assets (Images) Not Loading

**Symptom:**
- Images, fonts, or other assets show as broken

**Cause:**
- Assets not uploaded
- Wrong path references

**Solution:**
1. In File Manager, check that all files from `dist/assets/` are uploaded
2. Compare file list with your local `dist/` folder
3. Re-upload any missing files

### Issue: HTTPS Certificate Not Working

**Symptom:**
- Browser shows certificate warning
- Can't access HTTPS

**Cause:**
- Certificate installation failed
- Domain not pointing to server

**Solution:**
1. Verify domain DNS points to your VPS
2. Wait 24-48 hours for DNS propagation
3. Try installing certificate again:
   - **SSL/TLS Certificates** → **Install Certificate**
   - Select Let's Encrypt
   - Try again

### Issue: File Upload Hangs

**Symptom:**
- Upload shows progress but never completes
- Browser seems frozen

**Cause:**
- Large file size
- Network timeout
- Browser issue

**Solution:**
1. Close upload dialog
2. Try uploading fewer files at once
3. Try different browser
4. Check internet connection speed
5. Consider using SFTP instead (if available)

---

## Performance Optimization

### 8.1 Enable Gzip Compression

1. In Plesk **Web Hosting** → **Nginx Settings**
2. Add to custom configuration:

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_comp_level 6;
```

3. Click **OK**

This reduces file sizes by 60-70%.

### 8.2 Browser Caching

Already configured in Nginx settings we applied earlier. Static files cached for 1 year.

### 8.3 Monitor Performance

1. Use Lighthouse (Chrome Dev Tools F12)
2. Run audit on your domain
3. Should score 80+ on Performance
4. Fix any warnings

### 8.4 Use CDN (Optional)

For global performance:

1. Sign up for Cloudflare (free)
2. Point domain DNS to Cloudflare
3. Enable caching and optimization
4. Significantly faster for international users

---

## Backup & Maintenance

### 9.1 Set Up Backups in Plesk

1. Go to **Tools & Settings** → **Backup Manager**
2. Click **Backup Settings**
3. Configure:
   - Backup location: Local (default)
   - Backup retention: Keep last 7 days
   - Schedule: Daily at 2 AM

4. Click **OK**

### 9.2 Manual Backup

Anytime before updating:

1. **Backup Manager** → **Backup** tab
2. Select your domain
3. Click **Backup Now**
4. Wait for completion

### 9.3 Update Frontend

When you make code changes:

```bash
cd frontend
npm run build
# Upload new dist/ files to Plesk
# Old files are overwritten
```

---

## Quick Reference

### File Locations

| Item | Location |
|------|----------|
| Frontend files | `/var/www/vhosts/yourdomain.com/httpdocs/` |
| Nginx logs | `/var/log/nginx/error.log` |
| Access logs | `/var/log/nginx/access.log` |
| Plesk panel | `https://your-server:8443` |

### URLs

| Service | URL |
|---------|-----|
| Frontend | `https://yourdomain.com` |
| Backend | `https://api.yourdomain.com` |
| Plesk Panel | `https://your-server:8443` |

### Nginx Config Locations in Plesk

**For different Plesk versions:**

- **Plesk 18+**: **Web Hosting** → **Nginx Settings**
- **Plesk 17**: **Web Hosting** → **Nginx Configuration**
- **Plesk Obsidian**: **Web Hosting** → **Nginx & Apache Settings**

### Common Commands (via SSH, if needed)

```bash
# View Nginx error log
tail -f /var/log/nginx/error.log

# Check Nginx syntax
nginx -t

# Reload Nginx
systemctl reload nginx

# View Plesk file locations
ls -la /var/www/vhosts/yourdomain.com/httpdocs/
```

---

## Checklist: Pre-Launch

Before considering your frontend live:

- [ ] Frontend page loads without 404
- [ ] No JavaScript errors in console
- [ ] Page refresh works (not 404)
- [ ] Responsive design works on mobile
- [ ] SSL certificate installed (HTTPS works)
- [ ] Forms display correctly
- [ ] Can reach backend API (if configured)
- [ ] Load time is acceptable (<3 seconds)
- [ ] Static files loading (CSS, images, fonts)
- [ ] Navigation between pages works
- [ ] Mobile menu works on small screens

---

## Next Steps

### Immediately After Deployment:

1. ✅ Test all pages
2. ✅ Create test account (if backend ready)
3. ✅ Verify mobile experience
4. ✅ Check performance metrics

### Within First Week:

1. Monitor error logs
2. Invite team members
3. Configure team structure
4. Run simulations

### Ongoing:

1. Monitor performance
2. Regular backups
3. Update code as needed
4. Check logs for errors

---

## Getting Help

**For deployment issues:**
- Check troubleshooting section above
- Review Plesk logs: **Domains** → **Logs**
- Check Nginx error log (see Quick Reference)

**For frontend features:**
- See `FRONTEND_README.md`

**For backend integration:**
- Ensure backend API is running
- Check `VITE_API_URL` is correct in frontend
- Verify CORS enabled on backend

---

## Summary

You now have a complete, production-ready React frontend deployed to your Plesk VPS:

✅ Frontend files uploaded
✅ Nginx configured for React Router
✅ SSL certificate installed
✅ HTTPS enabled
✅ Performance optimized
✅ Ready for users

Your Baseball Manager AI dashboard is live! 🚀

---

**Need help?** Check the troubleshooting section or review earlier steps. Most issues are resolved by re-applying the Nginx configuration or re-uploading files.
