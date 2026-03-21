# Authentication Pages Testing Guide

## Prerequisites

1. Backend server must be running on `http://localhost:8000`
2. Frontend dev server must be running on `http://localhost:3000`
3. Database must be initialized with migrations

## Start Servers

### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

## Test Cases

### 1. Job Seeker Registration

**URL**: http://localhost:3000/register/job-seeker

**Test Case 1.1: Validation Errors**
- Leave all fields empty and submit
- Expected: Validation errors for all required fields

**Test Case 1.2: Weak Password**
- Email: `test@example.com`
- Full Name: `Test User`
- Password: `weak`
- Confirm Password: `weak`
- Expected: Password validation errors (missing uppercase, number, special char)

**Test Case 1.3: Password Mismatch**
- Email: `test@example.com`
- Full Name: `Test User`
- Password: `SecurePass123!`
- Confirm Password: `DifferentPass123!`
- Expected: "Passwords don't match" error

**Test Case 1.4: Successful Registration**
- Email: `jobseeker@test.com`
- Full Name: `John Doe`
- Phone: `+1234567890` (optional)
- Password: `SecurePass123!`
- Confirm Password: `SecurePass123!`
- Expected: 
  - Redirect to `/jobs`
  - Tokens stored in localStorage
  - User data in Zustand store

**Test Case 1.5: Duplicate Email**
- Use same email as Test Case 1.4
- Expected: "Email already registered" error

### 2. Employer Registration

**URL**: http://localhost:3000/register/employer

**Test Case 2.1: Validation Errors**
- Leave all fields empty and submit
- Expected: Validation errors for required fields

**Test Case 2.2: Invalid Website URL**
- Email: `employer@test.com`
- Company Name: `Test Corp`
- Company Website: `not-a-url`
- Password: `SecurePass123!`
- Confirm Password: `SecurePass123!`
- Expected: "Invalid URL" error for website field

**Test Case 2.3: Successful Registration**
- Email: `employer@test.com`
- Company Name: `Test Corporation`
- Company Website: `https://testcorp.com` (optional)
- Company Description: `A test company` (optional)
- Password: `SecurePass123!`
- Confirm Password: `SecurePass123!`
- Expected:
  - Redirect to `/employer/dashboard`
  - Tokens stored in localStorage
  - User data in Zustand store

**Test Case 2.4: Duplicate Email**
- Use same email as Test Case 2.3
- Expected: "Email already registered" error

### 3. Login

**URL**: http://localhost:3000/login

**Test Case 3.1: Validation Errors**
- Leave fields empty and submit
- Expected: Validation errors

**Test Case 3.2: Invalid Credentials**
- Email: `wrong@test.com`
- Password: `WrongPass123!`
- Expected: "Invalid email or password" error

**Test Case 3.3: Job Seeker Login**
- Email: `jobseeker@test.com` (from Test Case 1.4)
- Password: `SecurePass123!`
- Expected:
  - Redirect to `/jobs`
  - Tokens stored in localStorage

**Test Case 3.4: Employer Login**
- Email: `employer@test.com` (from Test Case 2.3)
- Password: `SecurePass123!`
- Expected:
  - Redirect to `/employer/dashboard`
  - Tokens stored in localStorage

**Test Case 3.5: Rate Limiting**
- Make 5+ failed login attempts rapidly
- Expected: "Too many login attempts" error with 429 status

### 4. Token Storage Verification

After successful login/registration:

1. Open browser DevTools (F12)
2. Go to Application/Storage tab
3. Check localStorage:
   - `accessToken` should be present
   - `refreshToken` should be present
4. Check Zustand store (in localStorage as `auth-storage`):
   - Should contain user object
   - Should contain tokens object
   - `isAuthenticated` should be `true`

### 5. Token Refresh (Manual Test)

**Option A: Wait for expiration**
1. Login successfully
2. Wait 15 minutes (access token expiration)
3. Make an authenticated API request
4. Check Network tab - should see automatic refresh request
5. Original request should succeed with new token

**Option B: Manual token invalidation**
1. Login successfully
2. Open DevTools → Application → localStorage
3. Delete or modify `accessToken`
4. Navigate to a protected page or make API request
5. Should automatically refresh token

### 6. Cross-Page Navigation

**Test Case 6.1: Login to Registration**
- Go to `/login`
- Click "Register as Job Seeker" link
- Expected: Navigate to `/register/job-seeker`

**Test Case 6.2: Registration to Login**
- Go to `/register/job-seeker`
- Click "Sign in" link
- Expected: Navigate to `/login`

## Verification Checklist

- [ ] Job seeker registration form validates all fields
- [ ] Employer registration form validates all fields
- [ ] Login form validates credentials
- [ ] Password strength requirements enforced
- [ ] Duplicate email detection works
- [ ] Tokens stored in localStorage after auth
- [ ] Role-based redirect works (employer vs job seeker)
- [ ] Error messages are user-friendly
- [ ] Forms are responsive on mobile
- [ ] All links between auth pages work
- [ ] Rate limiting prevents brute force attacks

## Common Issues

### Issue: "Network Error" or "Failed to fetch"
**Solution**: Ensure backend is running on http://localhost:8000

### Issue: CORS errors
**Solution**: Backend should have CORS configured for http://localhost:3000

### Issue: 404 on API endpoints
**Solution**: Check that API_BASE_PATH is set correctly in `.env.local`

### Issue: Tokens not persisting
**Solution**: Check browser localStorage is enabled and not in incognito mode

## Environment Variables

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api
```

## Success Criteria

All test cases pass and:
1. Users can register as job seekers or employers
2. Users can login with valid credentials
3. JWT tokens are stored and refreshed automatically
4. Form validation prevents invalid submissions
5. Error messages guide users to fix issues
6. Navigation between auth pages works smoothly
