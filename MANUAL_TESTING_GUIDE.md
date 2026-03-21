# Manual Testing Guide - Job Aggregation Platform

## Overview

This guide provides comprehensive manual testing procedures for the Job Aggregation and Posting Platform. It covers all user flows for both job seekers and employers, browser compatibility testing, mobile device testing, and accessibility testing.

**Task Reference:** Task 37.4 - Perform manual testing  
**Requirements Validated:** 20.1, 20.2, 20.3, 20.4, 20.5

## Table of Contents

1. [Testing Environment Setup](#testing-environment-setup)
2. [Job Seeker User Flows](#job-seeker-user-flows)
3. [Employer User Flows](#employer-user-flows)
4. [Browser Compatibility Testing](#browser-compatibility-testing)
5. [Mobile Device Testing](#mobile-device-testing)
6. [Accessibility Testing](#accessibility-testing)
7. [Test Results Documentation](#test-results-documentation)

---

## Testing Environment Setup

### Prerequisites

- Access to staging/production environment
- Test accounts created:
  - Job Seeker account (email: testseeker@example.com)
  - Employer account - Free tier (email: testemployer-free@example.com)
  - Employer account - Basic tier (email: testemployer-basic@example.com)
  - Employer account - Premium tier (email: testemployer-premium@example.com)
- Test data:
  - Sample resume file (PDF, < 5MB)
  - Sample cover letter text
  - Sample job posting data
  - Valid job URLs for import testing

### Test Browsers

- **Chrome:** Latest stable version (120+)
- **Firefox:** Latest stable version (120+)
- **Safari:** Latest stable version (17+)

### Test Devices

- **iOS:** iPhone 12 or later (iOS 16+)
- **Android:** Samsung Galaxy S21 or later (Android 12+)

---

## Job Seeker User Flows

### Flow 1: Registration and Login

**Test ID:** JS-001  
**Requirements:** 12.1, 12.2, 12.3, 12.4, 20.1, 20.2

#### Test Steps

1. **Navigate to Registration Page**
   - [ ] Open browser and navigate to `/register/job-seeker`
   - [ ] Verify page loads without errors
   - [ ] Verify responsive layout on current device

2. **Complete Registration Form**
   - [ ] Enter email address
   - [ ] Enter password (min 8 characters)
   - [ ] Enter full name
   - [ ] Enter phone number
   - [ ] Click "Register" button
   - [ ] Verify validation messages for invalid inputs
   - [ ] Verify successful registration redirects to login

3. **Login with New Account**
   - [ ] Navigate to `/login`
   - [ ] Enter registered email
   - [ ] Enter password
   - [ ] Click "Login" button
   - [ ] Verify successful login redirects to job search page
   - [ ] Verify JWT token is stored

4. **Test Session Persistence**
   - [ ] Refresh the page
   - [ ] Verify user remains logged in
   - [ ] Close and reopen browser
   - [ ] Verify session is maintained (if "Remember me" was checked)

**Expected Results:**
- Registration form validates all inputs correctly
- Successful registration creates account
- Login issues JWT tokens (access + refresh)
- Session persists across page refreshes
- Mobile layout is responsive and usable

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 2: Job Search and Filtering

**Test ID:** JS-002  
**Requirements:** 6.1-6.14, 20.1, 20.3

#### Test Steps

1. **Basic Search**
   - [ ] Navigate to `/jobs`
   - [ ] Enter search term in search box (e.g., "Software Engineer")
   - [ ] Click search button or press Enter
   - [ ] Verify results are displayed
   - [ ] Verify results are sorted by quality score (highest first)
   - [ ] Verify pagination controls are visible

2. **Apply Location Filter**
   - [ ] Select location from dropdown (e.g., "San Francisco, CA")
   - [ ] Click "Apply Filters"
   - [ ] Verify only jobs matching location are shown
   - [ ] Verify filter chip is displayed showing active filter

3. **Apply Job Type Filter**
   - [ ] Check "Full-time" checkbox
   - [ ] Check "Remote" checkbox
   - [ ] Click "Apply Filters"
   - [ ] Verify only full-time remote jobs are shown

4. **Apply Salary Range Filter**
   - [ ] Enter minimum salary (e.g., "$80,000")
   - [ ] Enter maximum salary (e.g., "$150,000")
   - [ ] Click "Apply Filters"
   - [ ] Verify only jobs within salary range are shown

5. **Apply Experience Level Filter**
   - [ ] Select "Mid-level" from experience dropdown
   - [ ] Click "Apply Filters"
   - [ ] Verify only mid-level jobs are shown

6. **Apply Posted Within Filter**
   - [ ] Select "Last 7 days" from posted within dropdown
   - [ ] Click "Apply Filters"
   - [ ] Verify only recent jobs are shown

7. **Test Multiple Filters Combined**
   - [ ] Apply location, job type, and salary filters together
   - [ ] Verify results match ALL filter criteria
   - [ ] Verify "Clear all filters" button works

8. **Test Pagination**
   - [ ] Scroll to bottom of results
   - [ ] Click "Next page" button
   - [ ] Verify page 2 results load
   - [ ] Verify URL updates with page parameter
   - [ ] Click "Previous page" button
   - [ ] Verify navigation works correctly

**Expected Results:**
- Search returns relevant results
- Each filter correctly narrows results
- Multiple filters work together (AND logic)
- Pagination works smoothly
- Touch targets are adequate on mobile (44x44px minimum)

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 3: View Job Details

**Test ID:** JS-003  
**Requirements:** 20.1, 20.3

#### Test Steps

1. **Open Job Details Page**
   - [ ] From search results, click on a job card
   - [ ] Verify navigation to `/jobs/[id]`
   - [ ] Verify job details page loads

2. **Verify Job Information Display**
   - [ ] Verify job title is displayed prominently
   - [ ] Verify company name is shown
   - [ ] Verify location is shown
   - [ ] Verify job type (Full-time, Remote, etc.) is shown
   - [ ] Verify salary range is displayed (if available)
   - [ ] Verify full job description is visible
   - [ ] Verify requirements list is visible
   - [ ] Verify responsibilities list is visible
   - [ ] Verify posted date is shown
   - [ ] Verify "Apply" button is visible (for direct posts)

3. **Test External Job Links**
   - [ ] For aggregated jobs, verify "View on [Platform]" link is present
   - [ ] Click external link
   - [ ] Verify it opens in new tab
   - [ ] Verify it navigates to correct external URL

4. **Test Featured Job Indicator**
   - [ ] Find a featured job
   - [ ] Verify featured badge/indicator is visible
   - [ ] Verify visual distinction from regular jobs

**Expected Results:**
- All job information displays correctly
- Layout is responsive on all screen sizes
- External links work correctly
- Featured jobs are visually distinguished

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 4: Job Application Submission

**Test ID:** JS-004  
**Requirements:** 7.1-7.12, 20.1, 20.2, 20.3

#### Test Steps

1. **Navigate to Application Page**
   - [ ] From job details page (direct post only), click "Apply Now"
   - [ ] Verify navigation to `/jobs/[id]/apply`
   - [ ] Verify application form loads

2. **Complete Application Form**
   - [ ] Verify resume upload field is present
   - [ ] Click "Upload Resume" button
   - [ ] Select PDF resume file (< 5MB)
   - [ ] Verify file name is displayed after upload
   - [ ] Enter cover letter text (optional)
   - [ ] Verify character count for cover letter

3. **Submit Application**
   - [ ] Click "Submit Application" button
   - [ ] Verify loading indicator appears
   - [ ] Verify success message is displayed
   - [ ] Verify redirect to applications page

4. **Test Validation**
   - [ ] Try submitting without resume
   - [ ] Verify error message: "Resume is required"
   - [ ] Try uploading file > 5MB
   - [ ] Verify error message: "File size exceeds limit"
   - [ ] Try uploading non-PDF file
   - [ ] Verify error message: "Only PDF files are allowed"

5. **Test Duplicate Application Prevention**
   - [ ] Try applying to same job again
   - [ ] Verify error message: "You have already applied to this job"

**Expected Results:**
- Application form is user-friendly and responsive
- File upload works correctly
- Validation prevents invalid submissions
- Success confirmation is clear
- Duplicate applications are prevented

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 5: View Application Status

**Test ID:** JS-005  
**Requirements:** 7.10, 7.11, 7.12, 20.1

#### Test Steps

1. **Navigate to Applications Page**
   - [ ] Click "My Applications" in navigation menu
   - [ ] Verify navigation to `/applications`
   - [ ] Verify applications list loads

2. **View Application List**
   - [ ] Verify all submitted applications are displayed
   - [ ] Verify each application shows:
     - [ ] Job title
     - [ ] Company name
     - [ ] Application date
     - [ ] Current status (Submitted, Reviewed, Shortlisted, etc.)
   - [ ] Verify applications are sorted by date (newest first)

3. **View Application Details**
   - [ ] Click on an application
   - [ ] Verify application details modal/page opens
   - [ ] Verify resume link is present
   - [ ] Verify cover letter is displayed (if provided)
   - [ ] Verify status history is shown (if available)

4. **Test Empty State**
   - [ ] Use account with no applications
   - [ ] Navigate to `/applications`
   - [ ] Verify empty state message is displayed
   - [ ] Verify "Browse Jobs" call-to-action is present

**Expected Results:**
- Applications list displays all submitted applications
- Status information is clear and up-to-date
- Application details are accessible
- Empty state is user-friendly

**Pass Criteria:** All checkboxes completed successfully

---

## Employer User Flows

### Flow 6: Employer Registration and Login

**Test ID:** EMP-001  
**Requirements:** 12.1, 12.2, 12.3, 12.4, 20.1, 20.2

#### Test Steps

1. **Navigate to Employer Registration**
   - [ ] Open browser and navigate to `/register/employer`
   - [ ] Verify page loads without errors
   - [ ] Verify responsive layout

2. **Complete Employer Registration Form**
   - [ ] Enter email address
   - [ ] Enter password (min 8 characters)
   - [ ] Enter company name
   - [ ] Enter company website (optional)
   - [ ] Upload company logo (optional)
   - [ ] Enter company description (optional)
   - [ ] Click "Register" button
   - [ ] Verify validation messages for invalid inputs
   - [ ] Verify successful registration

3. **Verify Default Subscription**
   - [ ] After registration, navigate to dashboard
   - [ ] Verify subscription tier is "Free"
   - [ ] Verify monthly post quota is displayed (3 posts)

4. **Login with Employer Account**
   - [ ] Navigate to `/login`
   - [ ] Enter employer email
   - [ ] Enter password
   - [ ] Click "Login" button
   - [ ] Verify redirect to employer dashboard

**Expected Results:**
- Registration form validates correctly
- Default free tier is assigned
- Login redirects to employer dashboard
- Mobile layout is responsive

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 7: Direct Job Posting

**Test ID:** EMP-002  
**Requirements:** 4.1-4.14, 8.4, 8.5, 8.6, 20.1, 20.2, 20.4

#### Test Steps

1. **Navigate to Job Posting Form**
   - [ ] From employer dashboard, click "Post a Job"
   - [ ] Verify navigation to `/employer/jobs/post`
   - [ ] Verify form loads correctly

2. **Complete Job Posting Form**
   - [ ] Enter job title (e.g., "Senior Software Engineer")
   - [ ] Enter company name (auto-filled from profile)
   - [ ] Enter location (e.g., "San Francisco, CA")
   - [ ] Check "Remote" checkbox (if applicable)
   - [ ] Select job type (Full-time, Part-time, Contract, etc.)
   - [ ] Select experience level (Entry, Mid, Senior, etc.)
   - [ ] Enter job description (min 50 characters)
   - [ ] Enter requirements (one per line or comma-separated)
   - [ ] Enter responsibilities (one per line or comma-separated)
   - [ ] Enter salary range (optional):
     - [ ] Minimum salary
     - [ ] Maximum salary
     - [ ] Currency
   - [ ] Select expiration date (max 90 days from today)
   - [ ] Add tags (optional)

3. **Test Form Validation**
   - [ ] Try submitting with title < 10 characters
   - [ ] Verify error: "Title must be at least 10 characters"
   - [ ] Try submitting with description < 50 characters
   - [ ] Verify error: "Description must be at least 50 characters"
   - [ ] Try submitting with salary_min > salary_max
   - [ ] Verify error: "Minimum salary must be less than maximum"
   - [ ] Try submitting with expiration date > 90 days
   - [ ] Verify error: "Expiration date cannot exceed 90 days"

4. **Submit Job Posting**
   - [ ] Fill all required fields correctly
   - [ ] Click "Post Job" button
   - [ ] Verify loading indicator appears
   - [ ] Verify success message is displayed
   - [ ] Verify redirect to job details or dashboard
   - [ ] Verify quota counter decrements

5. **Test Quota Enforcement (Free Tier)**
   - [ ] Post 3 jobs (free tier limit)
   - [ ] Try to post 4th job
   - [ ] Verify error: "Monthly posting quota exceeded"
   - [ ] Verify upgrade prompt is displayed

**Expected Results:**
- Form is intuitive and responsive
- Validation prevents invalid submissions
- Job is created successfully
- Quota is enforced correctly
- Mobile form is usable with appropriate input types

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 8: URL-Based Job Import

**Test ID:** EMP-003  
**Requirements:** 5.1-5.15, 20.1, 20.2, 20.4

#### Test Steps

1. **Navigate to URL Import Page**
   - [ ] From employer dashboard, click "Import from URL"
   - [ ] Verify navigation to `/employer/jobs/import`
   - [ ] Verify form loads correctly

2. **Submit Valid Job URL**
   - [ ] Enter valid job URL from whitelisted domain (e.g., LinkedIn, Indeed)
   - [ ] Click "Import Job" button
   - [ ] Verify loading indicator appears
   - [ ] Verify task ID is returned
   - [ ] Verify "Import in progress" message is displayed

3. **Monitor Import Progress**
   - [ ] Wait for import to complete (or poll status)
   - [ ] Verify success notification appears
   - [ ] Verify imported job appears in job list
   - [ ] Verify job details are correctly extracted

4. **Test URL Validation**
   - [ ] Try submitting invalid URL format
   - [ ] Verify error: "Invalid URL format"
   - [ ] Try submitting URL from non-whitelisted domain
   - [ ] Verify error: "Domain not supported for import"

5. **Test Duplicate Detection**
   - [ ] Try importing same URL again
   - [ ] Verify error: "This job already exists in our database"
   - [ ] Verify existing job ID is returned

6. **Test Import Quota**
   - [ ] Check current import quota
   - [ ] Import jobs until quota is reached
   - [ ] Try importing one more
   - [ ] Verify error: "Import quota exceeded"

**Expected Results:**
- URL import process is smooth
- Progress feedback is clear
- Validation prevents invalid imports
- Duplicate detection works correctly
- Quota enforcement works

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 9: Manage Job Postings

**Test ID:** EMP-004  
**Requirements:** 9.1-9.10, 10.6, 10.7, 20.1, 20.4

#### Test Steps

1. **View Job List**
   - [ ] Navigate to `/employer/jobs`
   - [ ] Verify all posted jobs are displayed
   - [ ] Verify each job shows:
     - [ ] Job title
     - [ ] Status (Active, Expired, Filled)
     - [ ] Application count
     - [ ] View count
     - [ ] Posted date
     - [ ] Expiration date
   - [ ] Verify jobs are sorted by posted date (newest first)

2. **Edit Job Posting**
   - [ ] Click "Edit" button on a job
   - [ ] Verify navigation to `/employer/jobs/[id]/edit`
   - [ ] Verify form is pre-filled with current data
   - [ ] Modify job title
   - [ ] Modify description
   - [ ] Click "Save Changes" button
   - [ ] Verify success message
   - [ ] Verify changes are reflected in job details

3. **Mark Job as Filled**
   - [ ] From job list, click "Mark as Filled" button
   - [ ] Verify confirmation dialog appears
   - [ ] Click "Confirm"
   - [ ] Verify job status changes to "Filled"
   - [ ] Verify job is no longer visible in public search

4. **Delete Job Posting**
   - [ ] From job list, click "Delete" button
   - [ ] Verify confirmation dialog appears
   - [ ] Click "Confirm"
   - [ ] Verify job status changes to "Deleted"
   - [ ] Verify job is removed from public search

5. **Reactivate Expired Job**
   - [ ] Find an expired job in the list
   - [ ] Click "Reactivate" button
   - [ ] Select new expiration date
   - [ ] Click "Reactivate Job" button
   - [ ] Verify job status changes to "Active"
   - [ ] Verify new expiration date is set

**Expected Results:**
- Job management interface is intuitive
- Edit functionality works correctly
- Status changes are reflected immediately
- Confirmation dialogs prevent accidental actions
- Mobile view is simplified and usable

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 10: Application Management

**Test ID:** EMP-005  
**Requirements:** 7.10, 7.11, 7.12, 9.4, 9.5, 20.1, 20.4

#### Test Steps

1. **View Applications for a Job**
   - [ ] From employer dashboard, click on a job with applications
   - [ ] Verify navigation to `/employer/applications?job=[id]`
   - [ ] Verify applications list loads
   - [ ] Verify each application shows:
     - [ ] Applicant name
     - [ ] Application date
     - [ ] Current status
     - [ ] Resume link

2. **View Application Details**
   - [ ] Click on an application
   - [ ] Verify application details modal/page opens
   - [ ] Verify applicant information is displayed
   - [ ] Verify resume download link works
   - [ ] Verify cover letter is displayed (if provided)

3. **Download Resume**
   - [ ] Click "Download Resume" button
   - [ ] Verify PDF file downloads
   - [ ] Verify file opens correctly

4. **Update Application Status**
   - [ ] Select an application
   - [ ] Change status from "Submitted" to "Reviewed"
   - [ ] Click "Update Status" button
   - [ ] Verify status updates successfully
   - [ ] Change status to "Shortlisted"
   - [ ] Verify status updates
   - [ ] Change status to "Rejected"
   - [ ] Verify status updates

5. **Add Employer Notes**
   - [ ] Select an application
   - [ ] Enter notes in "Employer Notes" field
   - [ ] Click "Save Notes" button
   - [ ] Verify notes are saved
   - [ ] Refresh page
   - [ ] Verify notes persist

6. **Filter Applications by Status**
   - [ ] Use status filter dropdown
   - [ ] Select "Shortlisted"
   - [ ] Verify only shortlisted applications are shown
   - [ ] Select "All"
   - [ ] Verify all applications are shown

**Expected Results:**
- Application management is efficient
- Resume downloads work correctly
- Status updates are immediate
- Notes functionality works
- Filtering helps organize applications

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 11: Subscription Management

**Test ID:** EMP-006  
**Requirements:** 8.1-8.12, 18.1-18.8, 20.1, 20.4

#### Test Steps

1. **View Current Subscription**
   - [ ] Navigate to `/employer/subscription`
   - [ ] Verify current tier is displayed (Free, Basic, or Premium)
   - [ ] Verify subscription details:
     - [ ] Monthly posts limit
     - [ ] Monthly posts used
     - [ ] Featured posts limit
     - [ ] Featured posts used
     - [ ] Subscription start date
     - [ ] Subscription end date (if applicable)

2. **View Subscription Tiers**
   - [ ] Verify all three tiers are displayed:
     - [ ] Free: 3 posts/month, 0 featured
     - [ ] Basic: 20 posts/month, 2 featured
     - [ ] Premium: Unlimited posts, 10 featured
   - [ ] Verify feature comparison table is clear
   - [ ] Verify pricing is displayed

3. **Upgrade Subscription (Free to Basic)**
   - [ ] Click "Upgrade to Basic" button
   - [ ] Verify redirect to Stripe checkout
   - [ ] Complete payment with test card (4242 4242 4242 4242)
   - [ ] Verify redirect back to platform
   - [ ] Verify subscription tier is updated to "Basic"
   - [ ] Verify quota limits are updated

4. **Upgrade Subscription (Basic to Premium)**
   - [ ] Click "Upgrade to Premium" button
   - [ ] Verify redirect to Stripe checkout
   - [ ] Complete payment
   - [ ] Verify subscription tier is updated to "Premium"
   - [ ] Verify quota limits are updated

5. **Test Payment Failure**
   - [ ] Try upgrading with declined test card (4000 0000 0000 0002)
   - [ ] Verify error message is displayed
   - [ ] Verify subscription tier remains unchanged

6. **Cancel Subscription**
   - [ ] Click "Cancel Subscription" button
   - [ ] Verify confirmation dialog appears
   - [ ] Click "Confirm Cancellation"
   - [ ] Verify cancellation is processed
   - [ ] Verify access remains until period end

**Expected Results:**
- Subscription information is clear
- Upgrade process is smooth
- Stripe integration works correctly
- Payment failures are handled gracefully
- Cancellation works correctly

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 12: Featured Listings

**Test ID:** EMP-007  
**Requirements:** 11.1-11.7, 20.1, 20.4

#### Test Steps

1. **Feature a Job Posting**
   - [ ] Navigate to job list
   - [ ] Select an active job
   - [ ] Click "Feature This Job" button
   - [ ] Verify confirmation dialog appears
   - [ ] Click "Confirm"
   - [ ] Verify featured flag is set
   - [ ] Verify featured quota is decremented

2. **Verify Featured Job Visibility**
   - [ ] Open job search page (as job seeker)
   - [ ] Perform a search
   - [ ] Verify featured jobs appear at top of results
   - [ ] Verify featured badge is visible on job card
   - [ ] Verify visual distinction (border, background, icon)

3. **Test Featured Quota Enforcement**
   - [ ] Feature jobs until quota is reached
   - [ ] Try to feature one more job
   - [ ] Verify error: "Featured post quota exceeded"
   - [ ] Verify upgrade prompt is displayed

4. **Unfeature a Job**
   - [ ] Select a featured job
   - [ ] Click "Remove Featured" button
   - [ ] Verify featured flag is removed
   - [ ] Verify quota is NOT refunded (as per business logic)

**Expected Results:**
- Featuring jobs is straightforward
- Featured jobs are prominently displayed
- Quota enforcement works
- Visual indicators are clear

**Pass Criteria:** All checkboxes completed successfully

---

### Flow 13: Analytics Dashboard (Premium Only)

**Test ID:** EMP-008  
**Requirements:** 8.12, 9.10, 19.6, 20.1, 20.4

#### Test Steps

1. **Access Analytics Dashboard**
   - [ ] Login with premium employer account
   - [ ] Navigate to `/employer/analytics`
   - [ ] Verify analytics page loads

2. **View Job Performance Metrics**
   - [ ] Verify metrics are displayed for each job:
     - [ ] Total views
     - [ ] Total applications
     - [ ] Views over time (chart)
     - [ ] Applications over time (chart)
     - [ ] Conversion rate (applications/views)

3. **Test Date Range Filter**
   - [ ] Select "Last 7 days" from date range dropdown
   - [ ] Verify charts update to show 7-day data
   - [ ] Select "Last 30 days"
   - [ ] Verify charts update
   - [ ] Select custom date range
   - [ ] Verify charts update

4. **Test Access Control**
   - [ ] Logout and login with free tier account
   - [ ] Try to navigate to `/employer/analytics`
   - [ ] Verify access is denied (HTTP 403 or redirect)
   - [ ] Verify upgrade prompt is displayed

**Expected Results:**
- Analytics provide valuable insights
- Charts are clear and interactive
- Date filtering works correctly
- Access control is enforced
- Mobile view is simplified

**Pass Criteria:** All checkboxes completed successfully

---

## Browser Compatibility Testing

### Test Matrix

**Test ID:** BROWSER-001  
**Requirements:** 20.1, 20.2, 20.3

Test each critical user flow on the following browsers:

| Flow | Chrome 120+ | Firefox 120+ | Safari 17+ | Status |
|------|-------------|--------------|------------|--------|
| Job Seeker Registration | [ ] | [ ] | [ ] | |
| Job Search & Filtering | [ ] | [ ] | [ ] | |
| Job Application | [ ] | [ ] | [ ] | |
| Employer Registration | [ ] | [ ] | [ ] | |
| Direct Job Posting | [ ] | [ ] | [ ] | |
| URL Job Import | [ ] | [ ] | [ ] | |
| Application Management | [ ] | [ ] | [ ] | |
| Subscription Management | [ ] | [ ] | [ ] | |

### Browser-Specific Checks

#### Chrome
- [ ] All forms submit correctly
- [ ] File uploads work
- [ ] Date pickers function properly
- [ ] Responsive design works at all breakpoints
- [ ] Console shows no errors

#### Firefox
- [ ] All forms submit correctly
- [ ] File uploads work
- [ ] Date pickers function properly
- [ ] Responsive design works at all breakpoints
- [ ] Console shows no errors

#### Safari
- [ ] All forms submit correctly
- [ ] File uploads work
- [ ] Date pickers function properly (Safari-specific styling)
- [ ] Responsive design works at all breakpoints
- [ ] Console shows no errors
- [ ] iOS-specific input types work correctly

**Expected Results:**
- All functionality works consistently across browsers
- No browser-specific bugs
- UI renders correctly in all browsers
- Performance is acceptable in all browsers

**Pass Criteria:** All checkboxes completed successfully for all browsers

---

## Mobile Device Testing

### iOS Testing (iPhone)

**Test ID:** MOBILE-IOS-001  
**Requirements:** 20.1, 20.2, 20.3, 20.5

#### Device Setup
- Device: iPhone 12 or later
- OS: iOS 16+
- Browser: Safari

#### Test Steps

1. **Responsive Layout**
   - [ ] Open platform on iPhone Safari
   - [ ] Navigate to homepage
   - [ ] Verify layout adapts to mobile screen
   - [ ] Verify no horizontal scrolling
   - [ ] Verify text is readable without zooming
   - [ ] Verify images scale appropriately

2. **Touch Interactions**
   - [ ] Verify all buttons are tappable (min 44x44px)
   - [ ] Verify tap targets don't overlap
   - [ ] Verify swipe gestures work (if applicable)
   - [ ] Verify pinch-to-zoom is disabled on form inputs
   - [ ] Verify dropdown menus work with touch

3. **Form Input Types**
   - [ ] Email field shows email keyboard
   - [ ] Phone field shows numeric keyboard
   - [ ] URL field shows URL keyboard
   - [ ] Date field shows date picker
   - [ ] Number field shows numeric keyboard

4. **Navigation**
   - [ ] Verify hamburger menu works (if applicable)
   - [ ] Verify navigation drawer opens/closes smoothly
   - [ ] Verify back button works correctly
   - [ ] Verify deep links work

5. **Job Search on Mobile**
   - [ ] Perform job search
   - [ ] Verify search results are readable
   - [ ] Verify filters are accessible
   - [ ] Verify job cards are tappable
   - [ ] Verify pagination works

6. **Job Application on Mobile**
   - [ ] Navigate to job application form
   - [ ] Verify form is usable on mobile
   - [ ] Test file upload from iOS
   - [ ] Verify camera/photo library access works
   - [ ] Submit application
   - [ ] Verify success message

7. **Employer Dashboard on Mobile**
   - [ ] Login as employer
   - [ ] Navigate to dashboard
   - [ ] Verify simplified mobile view
   - [ ] Verify job list is readable
   - [ ] Verify application management works
   - [ ] Test job posting form on mobile

**Expected Results:**
- Platform is fully functional on iOS
- Layout is responsive and readable
- Touch targets meet 44x44px minimum
- Input types trigger correct keyboards
- No iOS-specific bugs

**Pass Criteria:** All checkboxes completed successfully

---

### Android Testing

**Test ID:** MOBILE-ANDROID-001  
**Requirements:** 20.1, 20.2, 20.3, 20.5

#### Device Setup
- Device: Samsung Galaxy S21 or later
- OS: Android 12+
- Browser: Chrome

#### Test Steps

1. **Responsive Layout**
   - [ ] Open platform on Android Chrome
   - [ ] Navigate to homepage
   - [ ] Verify layout adapts to mobile screen
   - [ ] Verify no horizontal scrolling
   - [ ] Verify text is readable without zooming
   - [ ] Verify images scale appropriately

2. **Touch Interactions**
   - [ ] Verify all buttons are tappable (min 44x44px)
   - [ ] Verify tap targets don't overlap
   - [ ] Verify swipe gestures work (if applicable)
   - [ ] Verify long-press actions work (if applicable)
   - [ ] Verify dropdown menus work with touch

3. **Form Input Types**
   - [ ] Email field shows email keyboard
   - [ ] Phone field shows numeric keyboard
   - [ ] URL field shows URL keyboard
   - [ ] Date field shows date picker
   - [ ] Number field shows numeric keyboard

4. **Navigation**
   - [ ] Verify hamburger menu works (if applicable)
   - [ ] Verify navigation drawer opens/closes smoothly
   - [ ] Verify back button works correctly
   - [ ] Verify Android back button behavior

5. **Job Search on Mobile**
   - [ ] Perform job search
   - [ ] Verify search results are readable
   - [ ] Verify filters are accessible
   - [ ] Verify job cards are tappable
   - [ ] Verify pagination works

6. **Job Application on Mobile**
   - [ ] Navigate to job application form
   - [ ] Verify form is usable on mobile
   - [ ] Test file upload from Android
   - [ ] Verify file picker works
   - [ ] Submit application
   - [ ] Verify success message

7. **Employer Dashboard on Mobile**
   - [ ] Login as employer
   - [ ] Navigate to dashboard
   - [ ] Verify simplified mobile view
   - [ ] Verify job list is readable
   - [ ] Verify application management works
   - [ ] Test job posting form on mobile

8. **Performance on Mobile**
   - [ ] Verify page load times are acceptable (< 3s)
   - [ ] Verify smooth scrolling
   - [ ] Verify no lag when interacting with forms
   - [ ] Verify images load progressively

**Expected Results:**
- Platform is fully functional on Android
- Layout is responsive and readable
- Touch targets meet 44x44px minimum
- Input types trigger correct keyboards
- No Android-specific bugs
- Performance is acceptable

**Pass Criteria:** All checkboxes completed successfully

---

### Mobile Orientation Testing

**Test ID:** MOBILE-ORIENTATION-001  
**Requirements:** 20.1, 20.3

#### Test Steps (Both iOS and Android)

1. **Portrait to Landscape**
   - [ ] Open platform in portrait mode
   - [ ] Rotate device to landscape
   - [ ] Verify layout adapts correctly
   - [ ] Verify no content is cut off
   - [ ] Verify navigation remains accessible

2. **Landscape to Portrait**
   - [ ] Open platform in landscape mode
   - [ ] Rotate device to portrait
   - [ ] Verify layout adapts correctly
   - [ ] Verify no content is cut off
   - [ ] Verify navigation remains accessible

3. **Form Behavior During Rotation**
   - [ ] Fill out a form partially
   - [ ] Rotate device
   - [ ] Verify form data is preserved
   - [ ] Verify form remains usable

**Expected Results:**
- Layout adapts smoothly to orientation changes
- No data loss during rotation
- All functionality remains accessible

**Pass Criteria:** All checkboxes completed successfully

---

## Accessibility Testing

### Screen Reader Testing

**Test ID:** A11Y-001  
**Requirements:** 20.1, 20.2, 20.3, 20.4, 20.5

#### Setup
- **macOS:** VoiceOver (Cmd + F5)
- **Windows:** NVDA or JAWS
- **iOS:** VoiceOver (Settings > Accessibility)
- **Android:** TalkBack (Settings > Accessibility)

#### Test Steps

1. **Navigation with Screen Reader**
   - [ ] Enable screen reader
   - [ ] Navigate to homepage
   - [ ] Verify page title is announced
   - [ ] Use Tab key to navigate through interactive elements
   - [ ] Verify all interactive elements are reachable
   - [ ] Verify tab order is logical
   - [ ] Verify no keyboard traps exist

2. **Form Accessibility**
   - [ ] Navigate to registration form
   - [ ] Verify all form labels are announced
   - [ ] Verify required fields are indicated
   - [ ] Verify error messages are announced
   - [ ] Verify success messages are announced
   - [ ] Submit form using keyboard only
   - [ ] Verify form submission works

3. **Job Search Accessibility**
   - [ ] Navigate to job search page
   - [ ] Verify search input is labeled
   - [ ] Verify filter controls are accessible
   - [ ] Verify search results are announced
   - [ ] Verify result count is announced
   - [ ] Navigate through job cards with keyboard
   - [ ] Verify each job card content is readable

4. **Button and Link Accessibility**
   - [ ] Verify all buttons have descriptive labels
   - [ ] Verify all links have descriptive text
   - [ ] Verify icon-only buttons have aria-labels
   - [ ] Verify button states are announced (disabled, loading)

5. **Modal and Dialog Accessibility**
   - [ ] Open a modal dialog
   - [ ] Verify focus moves to modal
   - [ ] Verify modal content is announced
   - [ ] Verify Escape key closes modal
   - [ ] Verify focus returns to trigger element after close

6. **Image Accessibility**
   - [ ] Verify all images have alt text
   - [ ] Verify decorative images have empty alt text
   - [ ] Verify company logos have descriptive alt text

7. **Table Accessibility (if applicable)**
   - [ ] Navigate to page with data table
   - [ ] Verify table headers are announced
   - [ ] Verify table structure is clear
   - [ ] Verify table navigation works

**Expected Results:**
- All content is accessible via screen reader
- All interactive elements are keyboard accessible
- Tab order is logical
- Labels and descriptions are clear
- ARIA attributes are used correctly
- No accessibility barriers exist

**Pass Criteria:** All checkboxes completed successfully

---

### Keyboard Navigation Testing

**Test ID:** A11Y-002  
**Requirements:** 20.1, 20.3

#### Test Steps

1. **Basic Navigation**
   - [ ] Navigate entire site using only Tab key
   - [ ] Verify all interactive elements are reachable
   - [ ] Verify focus indicator is visible
   - [ ] Verify tab order is logical
   - [ ] Use Shift+Tab to navigate backwards
   - [ ] Verify backwards navigation works

2. **Form Navigation**
   - [ ] Navigate through form using Tab
   - [ ] Verify focus moves to next field
   - [ ] Use Enter to submit form
   - [ ] Verify submission works
   - [ ] Use Escape to cancel/close
   - [ ] Verify cancel works

3. **Dropdown and Select Navigation**
   - [ ] Focus on dropdown
   - [ ] Use Space or Enter to open
   - [ ] Use Arrow keys to navigate options
   - [ ] Use Enter to select option
   - [ ] Use Escape to close without selecting

4. **Modal Navigation**
   - [ ] Open modal using keyboard
   - [ ] Verify focus is trapped in modal
   - [ ] Navigate through modal content
   - [ ] Close modal using Escape
   - [ ] Verify focus returns correctly

5. **Skip Links**
   - [ ] Tab to first element on page
   - [ ] Verify "Skip to main content" link is visible
   - [ ] Activate skip link
   - [ ] Verify focus moves to main content

**Expected Results:**
- All functionality is accessible via keyboard
- Focus indicators are clear
- No keyboard traps
- Skip links work correctly

**Pass Criteria:** All checkboxes completed successfully

---

### Color Contrast and Visual Accessibility

**Test ID:** A11Y-003  
**Requirements:** 20.1

#### Test Steps

1. **Color Contrast Testing**
   - [ ] Use browser extension (e.g., WAVE, axe DevTools)
   - [ ] Scan homepage for contrast issues
   - [ ] Verify text meets WCAG AA standards (4.5:1 for normal text)
   - [ ] Verify large text meets WCAG AA standards (3:1)
   - [ ] Scan all major pages
   - [ ] Document any contrast failures

2. **Color Blindness Testing**
   - [ ] Use color blindness simulator (e.g., Colorblind Web Page Filter)
   - [ ] Test with Protanopia (red-blind)
   - [ ] Test with Deuteranopia (green-blind)
   - [ ] Test with Tritanopia (blue-blind)
   - [ ] Verify information is not conveyed by color alone
   - [ ] Verify status indicators use icons + color

3. **Text Scaling**
   - [ ] Increase browser text size to 200%
   - [ ] Verify layout doesn't break
   - [ ] Verify text remains readable
   - [ ] Verify no content is cut off
   - [ ] Verify interactive elements remain usable

4. **Focus Indicators**
   - [ ] Navigate site with keyboard
   - [ ] Verify focus indicators are visible on all elements
   - [ ] Verify focus indicators have sufficient contrast
   - [ ] Verify focus indicators are not obscured

**Expected Results:**
- Color contrast meets WCAG AA standards
- Information is not conveyed by color alone
- Text scaling works up to 200%
- Focus indicators are clear and visible

**Pass Criteria:** All checkboxes completed successfully

---

### ARIA and Semantic HTML Testing

**Test ID:** A11Y-004  
**Requirements:** 20.1

#### Test Steps

1. **Semantic HTML Structure**
   - [ ] Inspect page source
   - [ ] Verify proper heading hierarchy (h1, h2, h3, etc.)
   - [ ] Verify semantic elements are used (nav, main, article, aside, footer)
   - [ ] Verify lists use ul/ol/li elements
   - [ ] Verify buttons use <button> element
   - [ ] Verify links use <a> element

2. **ARIA Attributes**
   - [ ] Verify aria-label on icon-only buttons
   - [ ] Verify aria-describedby on form fields with help text
   - [ ] Verify aria-invalid on form fields with errors
   - [ ] Verify aria-live regions for dynamic content
   - [ ] Verify aria-expanded on expandable elements
   - [ ] Verify aria-hidden on decorative elements

3. **Form Accessibility**
   - [ ] Verify all inputs have associated labels
   - [ ] Verify fieldset/legend for grouped inputs
   - [ ] Verify required attribute on required fields
   - [ ] Verify autocomplete attributes where appropriate

4. **Landmark Regions**
   - [ ] Verify page has main landmark
   - [ ] Verify page has navigation landmark
   - [ ] Verify page has complementary landmark (if applicable)
   - [ ] Verify page has contentinfo landmark (footer)

**Expected Results:**
- Semantic HTML is used correctly
- ARIA attributes enhance accessibility
- Form elements are properly labeled
- Landmark regions are defined

**Pass Criteria:** All checkboxes completed successfully

---

## Test Results Documentation

### Test Execution Summary

**Date:** _______________  
**Tester:** _______________  
**Environment:** _______________

#### Overall Results

| Test Category | Total Tests | Passed | Failed | Blocked | Pass Rate |
|---------------|-------------|--------|--------|---------|-----------|
| Job Seeker Flows | 5 | | | | |
| Employer Flows | 8 | | | | |
| Browser Compatibility | 8 | | | | |
| Mobile Testing (iOS) | 1 | | | | |
| Mobile Testing (Android) | 1 | | | | |
| Accessibility | 4 | | | | |
| **TOTAL** | **27** | | | | |

---

### Defect Log

Use this template to document any issues found during testing:

#### Defect #1
- **Test ID:** _______________
- **Severity:** Critical / High / Medium / Low
- **Summary:** _______________
- **Steps to Reproduce:**
  1. _______________
  2. _______________
  3. _______________
- **Expected Result:** _______________
- **Actual Result:** _______________
- **Browser/Device:** _______________
- **Screenshot/Video:** _______________

#### Defect #2
- **Test ID:** _______________
- **Severity:** Critical / High / Medium / Low
- **Summary:** _______________
- **Steps to Reproduce:**
  1. _______________
  2. _______________
  3. _______________
- **Expected Result:** _______________
- **Actual Result:** _______________
- **Browser/Device:** _______________
- **Screenshot/Video:** _______________

---

### Requirements Validation

| Requirement | Status | Notes |
|-------------|--------|-------|
| 20.1 - Responsive layout on mobile | [ ] Pass [ ] Fail | |
| 20.2 - Appropriate input types on mobile | [ ] Pass [ ] Fail | |
| 20.3 - Touch-optimized interactions | [ ] Pass [ ] Fail | |
| 20.4 - Simplified employer dashboard on mobile | [ ] Pass [ ] Fail | |
| 20.5 - Touch targets min 44x44 pixels | [ ] Pass [ ] Fail | |

---

### Sign-Off

**Tester Signature:** _______________  
**Date:** _______________

**QA Lead Signature:** _______________  
**Date:** _______________

**Product Owner Signature:** _______________  
**Date:** _______________
