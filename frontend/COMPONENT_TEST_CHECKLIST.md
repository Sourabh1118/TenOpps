# Component Test Checklist

## Manual Testing Guide for Task 26.1 Components

### Prerequisites
1. Start the development server: `npm run dev` in the `frontend` directory
2. Open browser to `http://localhost:3000`

## Test Cases

### 1. MainLayout Component
- [ ] Visit home page (`/`)
- [ ] Verify header appears at top
- [ ] Verify footer appears at bottom
- [ ] Verify main content is between header and footer
- [ ] Scroll page and verify footer stays at bottom

### 2. Header Component - Desktop View

#### Public User (Not Logged In)
- [ ] Resize browser to desktop width (> 768px)
- [ ] Verify "JobHub" logo appears on left
- [ ] Verify navigation items appear: Home, Search Jobs, Login, Sign Up
- [ ] Hover over each link and verify hover effect (color change)
- [ ] Verify no hamburger menu icon visible
- [ ] Click "JobHub" logo and verify it navigates to home page

#### Authenticated Employer
- [ ] Log in as employer (you'll need to implement login first)
- [ ] Verify navigation shows: Home, Search Jobs, Post Job, Dashboard, Logout
- [ ] Verify "Sign Up" and "Login" are hidden
- [ ] Click "Logout" and verify it clears auth state

#### Authenticated Job Seeker
- [ ] Log in as job seeker
- [ ] Verify navigation shows: Home, Search Jobs, My Applications, Logout
- [ ] Verify employer-specific items (Post Job, Dashboard) are hidden

### 3. Header Component - Mobile View

#### Mobile Menu Toggle
- [ ] Resize browser to mobile width (< 768px)
- [ ] Verify hamburger menu icon (three lines) appears on right
- [ ] Verify desktop navigation is hidden
- [ ] Click hamburger icon
- [ ] Verify mobile menu opens below header
- [ ] Verify all navigation items appear in vertical list
- [ ] Click hamburger icon again (now shows X)
- [ ] Verify mobile menu closes

#### Mobile Menu Navigation
- [ ] Open mobile menu
- [ ] Click any navigation link
- [ ] Verify mobile menu automatically closes
- [ ] Verify navigation to correct page occurred

#### Mobile Menu - Authenticated
- [ ] Log in as employer
- [ ] Open mobile menu
- [ ] Verify employer-specific items appear
- [ ] Click "Logout"
- [ ] Verify menu closes and auth state cleared

### 4. Footer Component

#### Desktop View
- [ ] Resize browser to desktop width
- [ ] Verify four columns appear side by side
- [ ] Verify columns: JobHub, For Job Seekers, For Employers, Company
- [ ] Verify all links are present and styled correctly
- [ ] Hover over links and verify hover effect
- [ ] Verify copyright notice at bottom with current year

#### Mobile View
- [ ] Resize browser to mobile width
- [ ] Verify columns stack vertically
- [ ] Verify all content remains readable
- [ ] Verify spacing is appropriate

### 5. ProtectedRoute Component

#### Unauthenticated Access
- [ ] Log out (clear auth state)
- [ ] Try to access a protected route (you'll need to create one for testing)
- [ ] Verify redirect to `/login` occurs
- [ ] Verify loading spinner appears briefly during redirect

#### Authenticated Access
- [ ] Log in as any user
- [ ] Access a protected route (no role requirement)
- [ ] Verify content renders without redirect

#### Role-Based Access - Wrong Role
- [ ] Log in as job seeker
- [ ] Try to access employer-only route
- [ ] Verify redirect to appropriate page (not employer dashboard)

#### Role-Based Access - Correct Role
- [ ] Log in as employer
- [ ] Access employer-only route
- [ ] Verify content renders without redirect

### 6. Authentication State Management

#### Login Flow
- [ ] Open browser console
- [ ] Check localStorage for auth tokens (should be empty when logged out)
- [ ] Perform login (when login page is implemented)
- [ ] Verify `accessToken` and `refreshToken` appear in localStorage
- [ ] Verify `auth-storage` item appears in localStorage
- [ ] Refresh page
- [ ] Verify auth state persists (still logged in)

#### Logout Flow
- [ ] While logged in, open browser console
- [ ] Click "Logout" button
- [ ] Verify tokens are removed from localStorage
- [ ] Verify `auth-storage` is cleared
- [ ] Verify navigation updates to show Login/Sign Up
- [ ] Refresh page
- [ ] Verify user remains logged out

### 7. Responsive Design

#### Breakpoint Testing
- [ ] Start at desktop width (1200px+)
- [ ] Slowly resize browser to mobile width (320px)
- [ ] Verify smooth transition at 768px breakpoint
- [ ] Verify no layout breaks or overlapping elements
- [ ] Test at common device widths:
  - [ ] 320px (iPhone SE)
  - [ ] 375px (iPhone 12)
  - [ ] 768px (iPad)
  - [ ] 1024px (iPad Pro)
  - [ ] 1440px (Desktop)

### 8. Accessibility

#### Keyboard Navigation
- [ ] Use Tab key to navigate through header links
- [ ] Verify focus indicators are visible
- [ ] Verify all interactive elements are reachable
- [ ] Press Enter on focused link and verify navigation

#### Screen Reader (Optional)
- [ ] Enable screen reader (VoiceOver on Mac, NVDA on Windows)
- [ ] Navigate through header
- [ ] Verify all links are announced correctly
- [ ] Verify hamburger menu button has proper label

### 9. Visual Consistency

#### Styling
- [ ] Verify consistent blue theme (blue-600, blue-700, blue-800)
- [ ] Verify consistent spacing and padding
- [ ] Verify consistent font family (Geist Sans)
- [ ] Verify smooth transitions on hover states
- [ ] Verify no visual glitches or flashing

#### Cross-Browser Testing (Optional)
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test in Edge

## Known Limitations

1. **Login/Register Pages Not Yet Implemented**
   - Cannot fully test authenticated states
   - Can manually set auth state in browser console for testing:
   ```javascript
   localStorage.setItem('auth-storage', JSON.stringify({
     state: {
       user: { id: '1', email: 'test@example.com', role: 'employer' },
       tokens: { accessToken: 'test', refreshToken: 'test' },
       isAuthenticated: true
     }
   }))
   ```
   - Then refresh the page

2. **Protected Routes Not Yet Created**
   - Create test pages to verify ProtectedRoute functionality
   - Example test page:
   ```tsx
   // app/test-protected/page.tsx
   import { ProtectedRoute } from '@/components/auth'
   import { MainLayout } from '@/components/layout'
   
   export default function TestProtectedPage() {
     return (
       <ProtectedRoute>
         <MainLayout>
           <div className="container mx-auto px-4 py-8">
             <h1>Protected Page</h1>
             <p>You should only see this if logged in</p>
           </div>
         </MainLayout>
       </ProtectedRoute>
     )
   }
   ```

## Automated Testing (Future)

Consider adding these tests in the future:

1. **Unit Tests**
   - Test auth store functions (setAuth, clearAuth)
   - Test ProtectedRoute redirect logic
   - Test Header menu toggle

2. **Integration Tests**
   - Test full authentication flow
   - Test navigation between pages
   - Test role-based access control

3. **E2E Tests**
   - Test complete user journeys
   - Test responsive behavior
   - Test cross-browser compatibility

## Test Results

Date: ___________
Tester: ___________

| Test Case | Status | Notes |
|-----------|--------|-------|
| MainLayout | ⬜ Pass / ⬜ Fail | |
| Header Desktop | ⬜ Pass / ⬜ Fail | |
| Header Mobile | ⬜ Pass / ⬜ Fail | |
| Footer | ⬜ Pass / ⬜ Fail | |
| ProtectedRoute | ⬜ Pass / ⬜ Fail | |
| Auth State | ⬜ Pass / ⬜ Fail | |
| Responsive | ⬜ Pass / ⬜ Fail | |
| Accessibility | ⬜ Pass / ⬜ Fail | |

## Issues Found

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

## Recommendations

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________
