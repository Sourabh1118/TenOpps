# Manual Testing Guide: Job Application Interface

## Prerequisites
- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:3000`
- Test job seeker account created
- At least one direct job post available

## Test Setup

### 1. Create Test Accounts
```bash
# Job Seeker Account
Email: testseeker@example.com
Password: TestPassword123!

# Employer Account (for creating direct posts)
Email: testemployer@example.com
Password: TestPassword123!
```

### 2. Create Test Job (Direct Post)
- Login as employer
- Create a direct job post
- Note the job ID for testing

---

## Test Cases

### Test Case 1: View Application Form
**Objective:** Verify application form displays correctly

**Steps:**
1. Login as job seeker
2. Navigate to `/jobs`
3. Click on a direct job post
4. Click "Apply Now" button
5. Verify redirect to `/jobs/[id]/apply`

**Expected Results:**
- ✅ Application form displays
- ✅ Job title and company shown
- ✅ Resume upload field visible
- ✅ Cover letter textarea visible
- ✅ Submit and Cancel buttons visible

---

### Test Case 2: File Upload Validation - Valid File
**Objective:** Verify valid file uploads work

**Steps:**
1. Navigate to application form
2. Click file upload area
3. Select a PDF file < 5MB
4. Verify file name displays

**Expected Results:**
- ✅ File name appears in upload area
- ✅ No error messages
- ✅ Submit button enabled

**Test Files:**
- `test-resume.pdf` (< 5MB)
- `test-resume.doc` (< 5MB)
- `test-resume.docx` (< 5MB)

---

### Test Case 3: File Upload Validation - Invalid Size
**Objective:** Verify file size validation

**Steps:**
1. Navigate to application form
2. Select a file > 5MB
3. Try to submit

**Expected Results:**
- ✅ Error message: "Resume file size must be less than 5MB"
- ✅ Submit button disabled or shows error

---

### Test Case 4: File Upload Validation - Invalid Type
**Objective:** Verify file type validation

**Steps:**
1. Navigate to application form
2. Select a non-PDF/DOC/DOCX file (e.g., .txt, .jpg)
3. Try to submit

**Expected Results:**
- ✅ Error message: "Only PDF, DOC, and DOCX files are accepted"
- ✅ Submit button disabled or shows error

---

### Test Case 5: Submit Application - Success
**Objective:** Verify successful application submission

**Steps:**
1. Navigate to application form
2. Upload valid resume
3. Enter cover letter (optional)
4. Click "Submit Application"
5. Wait for submission

**Expected Results:**
- ✅ Upload progress indicator shows
- ✅ Progress goes from 0% to 100%
- ✅ Success message displays
- ✅ Message shows job title and company
- ✅ "View My Applications" button visible
- ✅ "Browse More Jobs" button visible

---

### Test Case 6: Submit Application - Already Applied
**Objective:** Verify duplicate application prevention

**Steps:**
1. Submit application to a job
2. Navigate back to same job
3. Try to apply again

**Expected Results:**
- ✅ Error message: "You have already applied to this job"
- ✅ Application not submitted

---

### Test Case 7: Apply to Aggregated Job
**Objective:** Verify aggregated jobs cannot be applied to

**Steps:**
1. Navigate to an aggregated job (sourceType !== 'direct')
2. Click "Apply Now" (should not be visible)
3. Or manually navigate to `/jobs/[id]/apply`

**Expected Results:**
- ✅ Warning message displays
- ✅ Message explains job is external
- ✅ "View Original Posting" button visible
- ✅ Link opens in new tab

---

### Test Case 8: View My Applications - Empty State
**Objective:** Verify empty state displays correctly

**Steps:**
1. Login as new job seeker (no applications)
2. Navigate to `/applications`

**Expected Results:**
- ✅ Empty state message displays
- ✅ Icon visible
- ✅ "No Applications Yet" heading
- ✅ "Browse Jobs" button visible

---

### Test Case 9: View My Applications - With Data
**Objective:** Verify applications list displays correctly

**Steps:**
1. Submit 2-3 applications
2. Navigate to `/applications`

**Expected Results:**
- ✅ All applications listed
- ✅ Job titles clickable
- ✅ Company names visible
- ✅ Locations with icons
- ✅ Status badges with correct colors
- ✅ Applied dates in relative format
- ✅ Resume links open in new tab
- ✅ Cover letters visible (if provided)
- ✅ Summary statistics at bottom

---

### Test Case 10: Application Status Badges
**Objective:** Verify all status badges display correctly

**Steps:**
1. Have applications with different statuses (use backend to update)
2. Navigate to `/applications`
3. Verify each status badge

**Expected Results:**
- ✅ SUBMITTED: Blue badge
- ✅ REVIEWED: Purple badge
- ✅ SHORTLISTED: Green badge
- ✅ REJECTED: Red badge
- ✅ ACCEPTED: Emerald badge

---

### Test Case 11: Authentication - Not Logged In
**Objective:** Verify authentication checks work

**Steps:**
1. Logout
2. Navigate to `/jobs/[id]/apply`

**Expected Results:**
- ✅ Warning message displays
- ✅ "Job Seeker Account Required" heading
- ✅ "Log In" button visible
- ✅ "Register" button visible

---

### Test Case 12: Authentication - Wrong Role
**Objective:** Verify role checks work

**Steps:**
1. Login as employer
2. Navigate to `/jobs/[id]/apply`

**Expected Results:**
- ✅ Warning message displays
- ✅ "Job Seeker Account Required" heading
- ✅ Cannot submit application

---

### Test Case 13: Navigation - Back to Job Details
**Objective:** Verify navigation works

**Steps:**
1. On application form
2. Click "Back to Job Details"

**Expected Results:**
- ✅ Redirects to `/jobs/[id]`
- ✅ Job details page displays

---

### Test Case 14: Navigation - Cancel Application
**Objective:** Verify cancel button works

**Steps:**
1. On application form
2. Fill out form partially
3. Click "Cancel"

**Expected Results:**
- ✅ Redirects to job details page
- ✅ Form data not saved

---

### Test Case 15: Navigation - After Success
**Objective:** Verify post-submission navigation

**Steps:**
1. Submit application successfully
2. Click "View My Applications"

**Expected Results:**
- ✅ Redirects to `/applications`
- ✅ New application visible in list

**Alternative:**
1. Submit application successfully
2. Click "Browse More Jobs"

**Expected Results:**
- ✅ Redirects to `/jobs`
- ✅ Job search page displays

---

### Test Case 16: Responsive Design - Mobile
**Objective:** Verify mobile layout

**Steps:**
1. Open application form on mobile (< 640px)
2. Check layout and usability

**Expected Results:**
- ✅ Form fits screen width
- ✅ Buttons stack vertically
- ✅ Text readable
- ✅ Touch targets adequate (44x44px)

---

### Test Case 17: Responsive Design - Tablet
**Objective:** Verify tablet layout

**Steps:**
1. Open application form on tablet (640-1024px)
2. Check layout and usability

**Expected Results:**
- ✅ Form uses available space
- ✅ Buttons side-by-side
- ✅ Grid layouts work correctly

---

### Test Case 18: Error Handling - Network Error
**Objective:** Verify network error handling

**Steps:**
1. Stop backend server
2. Try to submit application

**Expected Results:**
- ✅ Error message displays
- ✅ User can retry
- ✅ No crash or blank screen

---

### Test Case 19: Loading States
**Objective:** Verify loading indicators

**Steps:**
1. Navigate to `/applications` with slow network
2. Observe loading state

**Expected Results:**
- ✅ Skeleton loaders display
- ✅ Smooth transition to content
- ✅ No layout shift

---

### Test Case 20: Cover Letter - Optional
**Objective:** Verify cover letter is optional

**Steps:**
1. Submit application without cover letter
2. Check submission succeeds

**Expected Results:**
- ✅ Application submits successfully
- ✅ No error about missing cover letter

---

## Browser Compatibility Testing

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Performance Testing

### Metrics to Check
- [ ] Page load time < 2s
- [ ] Time to interactive < 3s
- [ ] File upload progress smooth
- [ ] No layout shifts (CLS < 0.1)
- [ ] Smooth animations (60fps)

---

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all form fields
- [ ] Submit with Enter key
- [ ] Cancel with Escape key
- [ ] File upload accessible via keyboard

### Screen Reader
- [ ] Form labels read correctly
- [ ] Error messages announced
- [ ] Success messages announced
- [ ] Status badges have proper labels

### Color Contrast
- [ ] Text meets WCAG AA standards
- [ ] Status badges readable
- [ ] Error messages visible

---

## Test Results Template

```
Test Date: ___________
Tester: ___________
Environment: ___________

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC1       | ✅/❌   |       |
| TC2       | ✅/❌   |       |
| ...       | ✅/❌   |       |

Issues Found:
1. 
2. 
3. 

Overall Status: PASS / FAIL
```

---

## Known Issues

### Issue 1: File Upload Placeholder
**Description:** Currently uses placeholder URL instead of actual file upload
**Impact:** Medium
**Workaround:** Implement real file upload service
**Status:** Planned for future enhancement

---

## Test Data

### Valid Resume Files
```
test-files/
  ├── resume-valid.pdf (2MB)
  ├── resume-valid.doc (1MB)
  └── resume-valid.docx (1.5MB)
```

### Invalid Resume Files
```
test-files/
  ├── resume-too-large.pdf (6MB)
  ├── resume-invalid.txt
  └── resume-invalid.jpg
```

### Sample Cover Letters
```
Short: "I am interested in this position."

Medium: "I am excited to apply for this position. I have 5 years of experience..."

Long: "Dear Hiring Manager, I am writing to express my strong interest..."
```

---

## Automated Testing Commands

```bash
# Run TypeScript checks
npm run build

# Run linter
npm run lint

# Run development server
npm run dev

# Build for production
npm run build
npm run start
```

---

## Reporting Issues

When reporting issues, include:
1. Test case number
2. Steps to reproduce
3. Expected result
4. Actual result
5. Screenshots/videos
6. Browser/device info
7. Console errors (if any)

**Example:**
```
Test Case: TC5
Steps: 
1. Navigate to /jobs/123/apply
2. Upload resume.pdf
3. Click Submit

Expected: Success message displays
Actual: Error message "Failed to submit"

Browser: Chrome 120.0
Device: Desktop
Console: TypeError: Cannot read property 'id' of undefined
```
