# Task 36.6: Configure Sentry for Error Tracking

**Requirement**: 19.1 - Error tracking and monitoring with Sentry

## Overview

Set up Sentry for comprehensive error tracking across:
- Backend API (FastAPI)
- Frontend (Next.js)
- Celery workers
- Performance monitoring
- Real-time alerts

## Prerequisites

- [ ] Backend deployed (Task 36.3)
- [ ] Frontend deployed (Task 36.5)
- [ ] Celery workers deployed (Task 36.4)
- [ ] Sentry account (https://sentry.io)

---

## Step 1: Create Sentry Account

### 1.1 Sign Up

1. Go to https://sentry.io
2. Click "Get Started"
3. Sign up with:
   - Email
   - GitHub (recommended)
   - Google

### 1.2 Create Organization

1. Enter organization name: `your-company`
2. Choose plan: **Developer** (Free)
   - 5,000 errors/month
   - 10,000 performance units/month
   - 1 team member
   - 30-day data retention

---

## Step 2: Create Backend Project

### 2.1 Create Python Project

1. Click "Create Project"
2. Select platform: **Python**
3. Set alert frequency: **Alert me on every new issue**
4. Project name: `job-platform-backend`
5. Team: Default
6. Click "Create Project"

### 2.2 Get Backend DSN

1. After project creation, copy the **DSN**:
   ```
   https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123
   ```
2. Save this - you'll need it for backend configuration

### 2.3 Skip Installation Wizard

- Click "Skip this onboarding"
- We'll configure manually

---

## Step 3: Configure Backend Sentry

### 3.1 Verify Sentry SDK Installed

Check `backend/requirements.txt`:
```txt
sentry-sdk[fastapi]==1.40.0
```

If not present, add it and redeploy.

### 3.2 Add DSN to Backend

1. **Railway**:
   - Go to backend service
   - Add environment variable:
     ```bash
     SENTRY_DSN=https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123
     ```
   - Railway auto-redeploys

2. **Render**:
   - Go to backend service
   - Environment → Add Variable
   - Key: `SENTRY_DSN`
   - Value: Your DSN
   - Click "Save"
   - Manually redeploy

### 3.3 Verify Backend Integration

Check `backend/app/main.py` has Sentry initialization:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,  # 10% of transactions
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
    )
```

### 3.4 Test Backend Error Reporting

1. **Add Test Endpoint** (temporary):
   ```python
   @app.get("/test-sentry")
   def test_sentry():
       raise Exception("Test Sentry error from backend")
   ```

2. **Trigger Error**:
   ```bash
   curl https://your-backend.up.railway.app/test-sentry
   ```

3. **Check Sentry Dashboard**:
   - Go to Sentry project
   - Click "Issues"
   - You should see: "Exception: Test Sentry error from backend"
   - Click on issue to see details:
     - Stack trace
     - Request data
     - Environment info
     - User context

4. **Remove Test Endpoint** after verification

---

## Step 4: Create Frontend Project

### 4.1 Create Next.js Project

1. In Sentry, click "Projects" → "Create Project"
2. Select platform: **Next.js**
3. Project name: `job-platform-frontend`
4. Click "Create Project"

### 4.2 Get Frontend DSN

1. Copy the **DSN**:
   ```
   https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124
   ```
2. Save for frontend configuration

---

## Step 5: Configure Frontend Sentry

### 5.1 Install Sentry SDK

```bash
cd frontend
npm install @sentry/nextjs
```

### 5.2 Run Sentry Wizard

```bash
npx @sentry/wizard@latest -i nextjs
```

Follow prompts:
1. **Login to Sentry**: Yes
2. **Select project**: job-platform-frontend
3. **Configure source maps**: Yes
4. **Create example page**: No

This creates:
- `sentry.client.config.js`
- `sentry.server.config.js`
- `sentry.edge.config.js`
- Updates `next.config.js`

### 5.3 Configure Sentry Files

**`sentry.client.config.js`**:
```javascript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124",
  environment: process.env.NEXT_PUBLIC_ENV || "development",
  tracesSampleRate: 0.1,
  debug: false,
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  integrations: [
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
});
```

**`sentry.server.config.js`**:
```javascript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124",
  environment: process.env.NEXT_PUBLIC_ENV || "development",
  tracesSampleRate: 0.1,
  debug: false,
});
```

### 5.4 Add Sentry DSN to Vercel

1. Go to Vercel project
2. **Settings** → **Environment Variables**
3. Add:
   ```bash
   SENTRY_DSN=https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124
   SENTRY_AUTH_TOKEN=your_sentry_auth_token
   SENTRY_ORG=your-org-name
   SENTRY_PROJECT=job-platform-frontend
   ```

4. Get auth token:
   - Go to Sentry → **Settings** → **Auth Tokens**
   - Click "Create New Token"
   - Scopes: `project:releases`, `org:read`
   - Copy token

### 5.5 Deploy Frontend

```bash
git add .
git commit -m "Add Sentry error tracking"
git push origin main
```

Vercel automatically deploys with Sentry integration.

### 5.6 Test Frontend Error Reporting

1. **Add Test Button** (temporary):
   ```typescript
   // In any page
   <button onClick={() => {
     throw new Error("Test Sentry error from frontend");
   }}>
     Test Sentry
   </button>
   ```

2. **Trigger Error**:
   - Visit your frontend
   - Click the test button
   - Error should be caught by Sentry

3. **Check Sentry Dashboard**:
   - Go to frontend project in Sentry
   - Click "Issues"
   - You should see the test error
   - View details:
     - Browser info
     - User actions (breadcrumbs)
     - Component stack
     - Session replay (if enabled)

4. **Remove Test Button** after verification

---

## Step 6: Configure Celery Workers

### 6.1 Add Sentry to Celery

Celery workers use the same backend DSN.

Verify `backend/app/tasks/celery_app.py` has:

```python
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1,
        integrations=[
            CeleryIntegration(),
        ],
    )
```

### 6.2 Verify Celery Configuration

Celery workers inherit `SENTRY_DSN` from environment variables (already set in Task 36.4).

### 6.3 Test Celery Error Reporting

1. **Create Test Task**:
   ```python
   @celery_app.task
   def test_sentry_task():
       raise Exception("Test Sentry error from Celery")
   ```

2. **Trigger Task**:
   ```python
   # From backend shell or API
   from app.tasks.celery_app import test_sentry_task
   test_sentry_task.delay()
   ```

3. **Check Sentry**:
   - Error should appear in backend project
   - Tagged with `celery` integration

---

## Step 7: Configure Alerts

### 7.1 Email Alerts

1. Go to Sentry project
2. **Settings** → **Alerts**
3. Click "Create Alert Rule"
4. Choose: **Issues**
5. Configure:
   - **When**: An event is seen
   - **If**: All events
   - **Then**: Send a notification to Team
   - **Via**: Email
6. Save rule

### 7.2 Slack Alerts (Optional)

1. **Settings** → **Integrations**
2. Find "Slack"
3. Click "Add to Slack"
4. Authorize Sentry
5. Choose Slack channel
6. Configure alert rules to use Slack

### 7.3 Alert Rules

Create rules for:

**Critical Errors**:
- Condition: Error level = error or fatal
- Action: Email + Slack
- Frequency: Immediately

**High Error Rate**:
- Condition: > 10 errors in 5 minutes
- Action: Email + Slack
- Frequency: Once per hour

**New Issues**:
- Condition: First seen
- Action: Email
- Frequency: Immediately

---

## Step 8: Configure Performance Monitoring

### 8.1 Enable Performance

Already enabled with `traces_sample_rate: 0.1` (10% of transactions).

### 8.2 View Performance Data

1. Go to Sentry project
2. Click "Performance"
3. View:
   - Transaction throughput
   - Response times (p50, p75, p95, p99)
   - Slow transactions
   - Database query performance

### 8.3 Optimize Sampling

Adjust sampling rates based on traffic:

**Low Traffic** (< 1000 req/day):
```python
traces_sample_rate=1.0  # 100%
```

**Medium Traffic** (1000-10000 req/day):
```python
traces_sample_rate=0.1  # 10%
```

**High Traffic** (> 10000 req/day):
```python
traces_sample_rate=0.01  # 1%
```

---

## Step 9: Configure Session Replay (Frontend)

### 9.1 Enable Replay

Already configured in `sentry.client.config.js`:
```javascript
replaysOnErrorSampleRate: 1.0,  // 100% of errors
replaysSessionSampleRate: 0.1,  // 10% of sessions
```

### 9.2 View Replays

1. Go to frontend project
2. Click "Replays"
3. View user sessions:
   - Mouse movements
   - Clicks
   - Scrolls
   - Console logs
   - Network requests

### 9.3 Privacy Settings

Ensure sensitive data is masked:
```javascript
new Sentry.Replay({
  maskAllText: true,        // Mask all text
  blockAllMedia: true,      // Block images/videos
  maskAllInputs: true,      // Mask form inputs
})
```

---

## Step 10: Monitor and Maintain

### 10.1 Daily Monitoring

1. **Check Dashboard**:
   - Go to Sentry dashboard
   - Review new issues
   - Check error trends

2. **Triage Issues**:
   - Mark as resolved
   - Assign to team members
   - Add comments
   - Link to GitHub issues

3. **Performance Review**:
   - Check slow transactions
   - Identify bottlenecks
   - Optimize as needed

### 10.2 Weekly Review

1. **Error Trends**:
   - Compare week-over-week
   - Identify patterns
   - Plan fixes

2. **Performance Trends**:
   - Response time trends
   - Database query performance
   - API endpoint performance

3. **User Impact**:
   - Affected users count
   - Error frequency per user
   - User feedback correlation

### 10.3 Release Tracking

1. **Tag Releases**:
   ```python
   sentry_sdk.init(
       dsn=settings.SENTRY_DSN,
       release="job-platform@1.0.0",
   )
   ```

2. **View Release Health**:
   - Go to **Releases**
   - See error rates per release
   - Compare releases
   - Track regressions

---

## Configuration Summary

### Backend Configuration

```bash
# Environment Variable
SENTRY_DSN=https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123

# Code (app/main.py)
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.APP_ENV,
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration(), SqlalchemyIntegration()],
)
```

### Frontend Configuration

```bash
# Vercel Environment Variables
SENTRY_DSN=https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124
SENTRY_AUTH_TOKEN=your_token
SENTRY_ORG=your-org
SENTRY_PROJECT=job-platform-frontend

# Code (sentry.client.config.js)
Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_ENV,
    tracesSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
})
```

### Celery Configuration

```python
# Uses same backend DSN
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.APP_ENV,
    integrations=[CeleryIntegration()],
)
```

---

## Testing Checklist

- [ ] Backend Sentry project created
- [ ] Frontend Sentry project created
- [ ] Backend DSN configured
- [ ] Frontend DSN configured
- [ ] Backend errors captured
- [ ] Frontend errors captured
- [ ] Celery errors captured
- [ ] Performance monitoring active
- [ ] Session replay working (frontend)
- [ ] Email alerts configured
- [ ] Slack alerts configured (optional)
- [ ] Release tracking enabled

---

## Troubleshooting

### Errors Not Appearing

**Problem**: Errors not showing in Sentry

**Solutions**:
1. Verify DSN is correct
2. Check `sentry_sdk.init()` is called
3. Verify environment variable is set
4. Check Sentry SDK is installed
5. Test with manual error:
   ```python
   sentry_sdk.capture_exception(Exception("Test"))
   ```

### Too Many Errors

**Problem**: Hitting free tier limit (5K errors/month)

**Solutions**:
1. Fix high-frequency errors first
2. Implement error grouping
3. Add error filtering:
   ```python
   def before_send(event, hint):
       # Filter out specific errors
       if 'ignorable_error' in str(hint.get('exc_info')):
           return None
       return event
   
   sentry_sdk.init(before_send=before_send)
   ```
4. Upgrade to paid plan if needed

### Performance Data Missing

**Problem**: No performance data in Sentry

**Solutions**:
1. Verify `traces_sample_rate` > 0
2. Check transactions are being created
3. Increase sample rate temporarily
4. Verify performance monitoring is enabled

### Source Maps Not Working

**Problem**: Frontend errors show minified code

**Solutions**:
1. Verify `SENTRY_AUTH_TOKEN` is set in Vercel
2. Check source maps are uploaded:
   ```bash
   # In build logs
   Uploading source maps to Sentry...
   ```
3. Verify `next.config.js` has Sentry plugin
4. Check Sentry project settings

---

## Free Tier Limits

### Sentry Developer Plan (Free)

- **Errors**: 5,000 events/month
- **Performance**: 10,000 transactions/month
- **Replays**: 50 replays/month
- **Team Members**: 1
- **Data Retention**: 30 days
- **Projects**: Unlimited
- **Cost**: $0/month

**Monitoring Usage**:
- Go to **Settings** → **Subscription**
- View current usage
- Set up alerts for approaching limits

**Optimization Tips**:
1. Use sampling for performance (10%)
2. Filter out noisy errors
3. Group similar errors
4. Fix high-frequency issues first

---

## Next Steps

After completing Sentry setup:

1. ✅ Sentry configured for backend
2. ✅ Sentry configured for frontend
3. ✅ Sentry configured for Celery
4. ✅ Alerts configured
5. ✅ Performance monitoring active
6. ✅ **All deployment tasks complete!**

---

## Support Resources

- **Sentry Documentation**: https://docs.sentry.io
- **Sentry Discord**: https://discord.gg/sentry
- **Sentry Status**: https://status.sentry.io
- **Best Practices**: https://docs.sentry.io/platforms/python/guides/fastapi/

---

**Task 36.6 Complete!** ✅

Your entire platform now has comprehensive error tracking and monitoring with Sentry!

---

# 🎉 All Deployment Tasks Complete!

You have successfully deployed:
- ✅ PostgreSQL Database (Supabase)
- ✅ Redis Instance (Railway/Render)
- ✅ FastAPI Backend (Railway/Render)
- ✅ Celery Workers (Railway/Render)
- ✅ Next.js Frontend (Vercel)
- ✅ Sentry Error Tracking

**Your Job Aggregation Platform is now live!** 🚀
