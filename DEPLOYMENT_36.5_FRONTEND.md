# Task 36.5: Deploy Next.js Frontend

**Requirement**: 16.5 - Frontend deployment with CDN, environment variables, and custom domain

## Overview

Deploy Next.js 14 frontend on Vercel's free tier with:
- Automatic deployments from GitHub
- Global CDN distribution
- SSL/HTTPS enabled
- Environment variable management
- Preview deployments for PRs
- Custom domain support

## Prerequisites

- [ ] Backend deployed (Task 36.3)
- [ ] Vercel account (https://vercel.com)
- [ ] GitHub repository with frontend code
- [ ] Backend API URL from Task 36.3

---

## Step 1: Prepare Frontend for Deployment

### 1.1 Update Environment Variables

Create `frontend/.env.production`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_API_BASE_PATH=/api

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key

# Environment
NEXT_PUBLIC_ENV=production

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true

# Analytics (optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

### 1.2 Verify next.config.js

Ensure `frontend/next.config.js` is configured:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: true,
  swcMinify: true,
  poweredByHeader: false,
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  
  // Image optimization
  images: {
    domains: ['your-backend.up.railway.app', 'supabase.co'],
    formats: ['image/avif', 'image/webp'],
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'origin-when-cross-origin' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
```

### 1.3 Verify vercel.json

Check `frontend/vercel.json`:

```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "headers": [
    {
      "source": "/_next/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 1.4 Commit and Push

```bash
cd frontend
git add .
git commit -m "Configure for Vercel deployment"
git push origin main
```

---

## Step 2: Import Project to Vercel

### 2.1 Sign in to Vercel

1. Go to https://vercel.com
2. Click "Sign Up" or "Login"
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your repositories

### 2.2 Import Repository

1. Click "Add New" → "Project"
2. Find your repository in the list
3. Click "Import"

### 2.3 Configure Project

1. **Framework Preset**: Next.js (auto-detected)
2. **Root Directory**: `frontend`
   - Click "Edit" next to Root Directory
   - Enter: `frontend`
3. **Build Settings**:
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

---

## Step 3: Configure Environment Variables

### 3.1 Add Environment Variables

1. Click "Environment Variables" section
2. Add each variable:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_API_BASE_PATH=/api

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key

# Environment
NEXT_PUBLIC_ENV=production

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true

# Analytics (optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

### 3.2 Environment Scopes

For each variable, select:
- ✅ **Production** (required)
- ✅ **Preview** (optional, for PR previews)
- ⬜ **Development** (not needed)

### 3.3 Sensitive Variables

For sensitive values (API keys):
- Use Vercel's "Sensitive" checkbox
- Values will be hidden after saving

---

## Step 4: Deploy

### 4.1 Trigger Deployment

1. Click "Deploy" button
2. Vercel starts building:
   - Installing dependencies
   - Running build command
   - Optimizing assets
   - Deploying to CDN

### 4.2 Monitor Build

1. Watch build logs in real-time
2. Look for:
   ```
   Installing dependencies...
   Running "npm run build"...
   Creating an optimized production build...
   Collecting page data...
   Generating static pages...
   Finalizing page optimization...
   Build completed successfully!
   ```

3. Build time: 2-5 minutes (first deployment)

### 4.3 Deployment Complete

1. Vercel shows success message
2. Provides deployment URL:
   ```
   https://your-project.vercel.app
   ```
3. Click "Visit" to open your site

---

## Step 5: Get Deployment URL

### 5.1 Production URL

Vercel provides:
- **Production**: `https://your-project.vercel.app`
- **Preview**: `https://your-project-git-branch.vercel.app` (for each branch)
- **Deployment**: `https://your-project-hash.vercel.app` (unique per deployment)

### 5.2 Save Production URL

```bash
# Frontend Production URL
FRONTEND_URL=https://your-project.vercel.app

# Save this for:
# - Backend CORS configuration
# - Stripe redirect URLs
# - OAuth callbacks
# - Testing
```

---

## Step 6: Update Backend CORS

### 6.1 Add Frontend URL to CORS

1. Go to Railway/Render backend service
2. Update `CORS_ORIGINS` environment variable:
   ```bash
   CORS_ORIGINS=https://your-project.vercel.app
   ```

3. If using custom domain, add both:
   ```bash
   CORS_ORIGINS=https://your-project.vercel.app,https://yourplatform.com
   ```

### 6.2 Redeploy Backend

1. Railway: Automatically redeploys on variable change
2. Render: Click "Manual Deploy" → "Deploy latest commit"

### 6.3 Verify CORS

Test from browser console on your frontend:
```javascript
fetch('https://your-backend.up.railway.app/api/jobs/search?query=developer')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err))
```

Should work without CORS errors.

---

## Step 7: Configure Custom Domain (Optional)

### 7.1 Add Domain to Vercel

1. In Vercel project, go to **Settings** → **Domains**
2. Click "Add Domain"
3. Enter your domain:
   - `yourplatform.com`
   - `www.yourplatform.com`

### 7.2 Configure DNS

Vercel provides DNS instructions:

**For Root Domain** (`yourplatform.com`):
```
Type: A
Name: @
Value: 76.76.21.21
```

**For WWW Subdomain** (`www.yourplatform.com`):
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

### 7.3 Add DNS Records

1. Go to your domain registrar (Namecheap, GoDaddy, etc.)
2. Find DNS settings
3. Add the records provided by Vercel
4. Save changes

### 7.4 Wait for Propagation

- DNS propagation: 5 minutes to 48 hours
- Usually completes in 1-2 hours
- Check status in Vercel dashboard

### 7.5 SSL Certificate

- Vercel automatically provisions SSL certificate
- Uses Let's Encrypt
- Renews automatically
- HTTPS enabled immediately after DNS propagation

---

## Step 8: Test Frontend Functionality

### 8.1 Basic Tests

1. **Homepage Loads**:
   - Visit `https://your-project.vercel.app`
   - Check for errors in browser console
   - Verify layout renders correctly

2. **API Connection**:
   - Open browser DevTools → Network tab
   - Navigate to job search page
   - Verify API calls to backend succeed

3. **Authentication**:
   - Try registering a new account
   - Try logging in
   - Verify JWT token is stored

4. **Job Search**:
   - Search for jobs
   - Apply filters
   - Verify results display

5. **Job Application**:
   - Click on a job
   - Try applying (if direct post)
   - Verify application submits

### 8.2 Performance Tests

1. **Lighthouse Audit**:
   - Open Chrome DevTools
   - Go to Lighthouse tab
   - Run audit
   - Target scores:
     - Performance: > 90
     - Accessibility: > 90
     - Best Practices: > 90
     - SEO: > 90

2. **Page Load Speed**:
   - First load: < 3 seconds
   - Subsequent loads: < 1 second
   - Check in Network tab

### 8.3 Mobile Tests

1. Open on mobile device
2. Test responsive layout
3. Test touch interactions
4. Verify forms work on mobile

---

## Step 9: Configure Automatic Deployments

### 9.1 Production Deployments

Vercel automatically deploys when you push to main branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Vercel:
1. Detects push
2. Starts build
3. Deploys to production
4. Updates `your-project.vercel.app`

### 9.2 Preview Deployments

For pull requests, Vercel creates preview deployments:

1. Create feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes and push:
   ```bash
   git push origin feature/new-feature
   ```

3. Create pull request on GitHub

4. Vercel automatically:
   - Builds preview deployment
   - Comments on PR with preview URL
   - Updates preview on each push

5. Preview URL:
   ```
   https://your-project-git-feature-new-feature.vercel.app
   ```

### 9.3 Deployment Notifications

Configure notifications:
1. Go to **Settings** → **Notifications**
2. Enable:
   - Deployment started
   - Deployment succeeded
   - Deployment failed
3. Choose channels:
   - Email
   - Slack
   - Discord

---

## Configuration Summary

### Environment Variables

```bash
# Production Environment Variables
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_API_BASE_PATH=/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true
```

### Deployment URLs

```bash
# Vercel URLs
Production: https://your-project.vercel.app
Preview: https://your-project-git-branch.vercel.app
Custom Domain: https://yourplatform.com (optional)

# Backend URL (for CORS)
Backend: https://your-backend.up.railway.app
```

---

## Testing Checklist

- [ ] Frontend deployed successfully
- [ ] Site loads at production URL
- [ ] No console errors
- [ ] API calls to backend work
- [ ] CORS configured correctly
- [ ] Authentication flow works
- [ ] Job search works
- [ ] Job application works
- [ ] Mobile responsive
- [ ] Lighthouse scores > 90
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active

---

## Troubleshooting

### Build Fails

**Problem**: Vercel build fails

**Solutions**:
1. Check build logs for specific error
2. Verify `package.json` scripts:
   ```json
   {
     "scripts": {
       "build": "next build",
       "start": "next start"
     }
   }
   ```
3. Test build locally:
   ```bash
   cd frontend
   npm run build
   ```
4. Check for TypeScript errors
5. Verify all dependencies in `package.json`

### API Calls Fail

**Problem**: Frontend can't connect to backend

**Solutions**:
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check backend CORS includes frontend URL
3. Test backend health:
   ```bash
   curl https://your-backend.up.railway.app/health
   ```
4. Check browser console for specific error

### Environment Variables Not Working

**Problem**: Environment variables undefined

**Solutions**:
1. Verify variables start with `NEXT_PUBLIC_`
2. Check variables are set in Vercel dashboard
3. Redeploy after adding variables
4. Check variable scope (Production/Preview)

### Custom Domain Not Working

**Problem**: Custom domain doesn't resolve

**Solutions**:
1. Verify DNS records are correct
2. Wait for DNS propagation (up to 48 hours)
3. Check domain status in Vercel dashboard
4. Use DNS checker: https://dnschecker.org
5. Verify domain is not already in use

### Slow Page Loads

**Problem**: Pages load slowly

**Solutions**:
1. Enable image optimization
2. Implement code splitting
3. Use dynamic imports
4. Enable caching headers
5. Optimize bundle size:
   ```bash
   npm run build
   # Check bundle size in output
   ```

---

## Performance Optimization

### 1. Image Optimization

```javascript
// Use Next.js Image component
import Image from 'next/image'

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={50}
  priority
/>
```

### 2. Code Splitting

```javascript
// Dynamic imports for heavy components
import dynamic from 'next/dynamic'

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
  ssr: false
})
```

### 3. Caching

```javascript
// API route with caching
export async function GET(request) {
  return NextResponse.json(data, {
    headers: {
      'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=30'
    }
  })
}
```

### 4. Bundle Analysis

```bash
# Install bundle analyzer
npm install @next/bundle-analyzer

# Add to next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer(nextConfig)

# Run analysis
ANALYZE=true npm run build
```

---

## Free Tier Limits

### Vercel Free Tier

- **Bandwidth**: 100GB/month
- **Build Time**: 6000 minutes/month
- **Deployments**: Unlimited
- **Team Members**: 1
- **Custom Domains**: Unlimited
- **SSL**: Included
- **CDN**: Global
- **Cost**: $0/month

**Monitoring Usage**:
- Go to **Settings** → **Usage**
- View current bandwidth and build minutes
- Set up alerts for approaching limits

---

## Next Steps

After completing frontend deployment:

1. ✅ Frontend deployed on Vercel
2. ✅ Backend CORS updated
3. ✅ Custom domain configured (optional)
4. ✅ All features tested
5. ➡️ **Next**: Configure Sentry (Task 36.6)
6. ➡️ Set up monitoring and analytics

---

## Support Resources

- **Vercel Documentation**: https://vercel.com/docs
- **Next.js Documentation**: https://nextjs.org/docs
- **Vercel Support**: https://vercel.com/support
- **Vercel Discord**: https://discord.gg/vercel

---

**Task 36.5 Complete!** ✅

Your Next.js frontend is now live and serving users globally via Vercel's CDN!
