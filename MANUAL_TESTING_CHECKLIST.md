# Manual Testing Checklist - Quick Reference

**Task:** 37.4 Perform manual testing  
**Requirements:** 20.1, 20.2, 20.3, 20.4, 20.5

## Job Seeker Flows

### ✅ Registration & Login (JS-001)
- [ ] Registration form works
- [ ] Validation messages display
- [ ] Login successful
- [ ] Session persists

### ✅ Job Search (JS-002)
- [ ] Basic search works
- [ ] Location filter works
- [ ] Job type filter works
- [ ] Salary filter works
- [ ] Experience filter works
- [ ] Posted within filter works
- [ ] Multiple filters work together
- [ ] Pagination works

### ✅ Job Details (JS-003)
- [ ] Job details page loads
- [ ] All information displays
- [ ] External links work
- [ ] Featured jobs are distinguished

### ✅ Job Application (JS-004)
- [ ] Application form loads
- [ ] Resume upload works
- [ ] Form validation works
- [ ] Application submits successfully
- [ ] Duplicate prevention works

### ✅ Application Status (JS-005)
- [ ] Applications list displays
- [ ] Application details accessible
- [ ] Status information clear
- [ ] Empty state displays

---

## Employer Flows

### ✅ Employer Registration (EMP-001)
- [ ] Registration form works
- [ ] Default free tier assigned
- [ ] Login redirects to dashboard

### ✅ Direct Job Posting (EMP-002)
- [ ] Job posting form loads
- [ ] Form validation works
- [ ] Job posts successfully
- [ ] Quota enforced

### ✅ URL Import (EMP-003)
- [ ] URL import form works
- [ ] Valid URLs import successfully
- [ ] Invalid URLs rejected
- [ ] Duplicate detection works
- [ ] Quota enforced

### ✅ Manage Jobs (EMP-004)
- [ ] Job list displays
- [ ] Edit job works
- [ ] Mark as filled works
- [ ] Delete job works
- [ ] Reactivate expired job works

### ✅ Application Management (EMP-005)
- [ ] Applications list displays
- [ ] Application details accessible
- [ ] Resume download works
- [ ] Status updates work
- [ ] Employer notes work
- [ ] Filtering works

### ✅ Subscription Management (EMP-006)
- [ ] Current subscription displays
- [ ] Tier comparison clear
- [ ] Upgrade to Basic works
- [ ] Upgrade to Premium works
- [ ] Payment failure handled
- [ ] Cancellation works

### ✅ Featured Listings (EMP-007)
- [ ] Feature job works
- [ ] Featured jobs visible in search
- [ ] Quota enforced
- [ ] Unfeature works

### ✅ Analytics (EMP-008)
- [ ] Analytics page loads (Premium only)
- [ ] Metrics display correctly
- [ ] Date filtering works
- [ ] Access control enforced

---

## Browser Compatibility

### ✅ Chrome 120+
- [ ] All forms work
- [ ] File uploads work
- [ ] Responsive design works
- [ ] No console errors

### ✅ Firefox 120+
- [ ] All forms work
- [ ] File uploads work
- [ ] Responsive design works
- [ ] No console errors

### ✅ Safari 17+
- [ ] All forms work
- [ ] File uploads work
- [ ] Date pickers work
- [ ] Responsive design works
- [ ] No console errors

---

## Mobile Testing

### ✅ iOS (iPhone)
- [ ] Responsive layout works
- [ ] Touch targets ≥ 44x44px
- [ ] Correct keyboard types
- [ ] Navigation works
- [ ] Job search works
- [ ] Job application works
- [ ] Employer dashboard works

### ✅ Android
- [ ] Responsive layout works
- [ ] Touch targets ≥ 44x44px
- [ ] Correct keyboard types
- [ ] Navigation works
- [ ] Job search works
- [ ] Job application works
- [ ] Employer dashboard works

### ✅ Orientation
- [ ] Portrait to landscape works
- [ ] Landscape to portrait works
- [ ] Form data preserved

---

## Accessibility

### ✅ Screen Reader
- [ ] Navigation works
- [ ] Forms accessible
- [ ] Job search accessible
- [ ] Buttons/links labeled
- [ ] Modals accessible
- [ ] Images have alt text

### ✅ Keyboard Navigation
- [ ] All elements reachable
- [ ] Focus indicators visible
- [ ] Tab order logical
- [ ] Forms navigable
- [ ] Dropdowns work
- [ ] Modals work
- [ ] Skip links work

### ✅ Visual Accessibility
- [ ] Color contrast meets WCAG AA
- [ ] Color blindness tested
- [ ] Text scales to 200%
- [ ] Focus indicators clear

### ✅ Semantic HTML
- [ ] Heading hierarchy correct
- [ ] Semantic elements used
- [ ] ARIA attributes correct
- [ ] Forms properly labeled
- [ ] Landmark regions defined

---

## Requirements Validation

- [ ] **20.1** - Responsive layout on mobile ✓
- [ ] **20.2** - Appropriate input types on mobile ✓
- [ ] **20.3** - Touch-optimized interactions ✓
- [ ] **20.4** - Simplified employer dashboard on mobile ✓
- [ ] **20.5** - Touch targets minimum 44x44 pixels ✓

---

## Sign-Off

**Date:** _______________  
**Tester:** _______________  
**Status:** [ ] Pass [ ] Fail  
**Notes:** _______________
