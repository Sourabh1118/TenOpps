# Manual Testing - Test Data Setup Guide

## Overview

This guide helps you prepare test data and accounts needed for comprehensive manual testing of the Job Aggregation Platform.

**Task:** 37.4 Perform manual testing  
**Related Documents:**
- MANUAL_TESTING_GUIDE.md (detailed test procedures)
- MANUAL_TESTING_CHECKLIST.md (quick reference)

---

## Test Accounts

### Job Seeker Accounts

Create the following job seeker test accounts:

#### Account 1: Basic Job Seeker
```
Email: testseeker1@example.com
Password: TestPass123!
Full Name: John Doe
Phone: +1-555-0101
```

#### Account 2: Active Job Seeker (with applications)
```
Email: testseeker2@example.com
Password: TestPass123!
Full Name: Jane Smith
Phone: +1-555-0102
```

#### Account 3: New Job Seeker (no activity)
```
Email: testseeker3@example.com
Password: TestPass123!
Full Name: Bob Johnson
Phone: +1-555-0103
```

---

### Employer Accounts

Create the following employer test accounts:

#### Account 1: Free Tier Employer
```
Email: employer-free@example.com
Password: TestPass123!
Company Name: TechStart Inc
Company Website: https://techstart.example.com
Subscription: Free (3 posts/month, 0 featured)
```

#### Account 2: Basic Tier Employer
```
Email: employer-basic@example.com
Password: TestPass123!
Company Name: GrowthCo LLC
Company Website: https://growthco.example.com
Subscription: Basic (20 posts/month, 2 featured)
```

#### Account 3: Premium Tier Employer
```
Email: employer-premium@example.com
Password: TestPass123!
Company Name: Enterprise Solutions Corp
Company Website: https://enterprise.example.com
Subscription: Premium (unlimited posts, 10 featured)
```

#### Account 4: Employer with Active Jobs
```
Email: employer-active@example.com
Password: TestPass123!
Company Name: ActiveHire Inc
Company Website: https://activehire.example.com
Subscription: Basic
Note: Should have 5+ active job postings with applications
```

---

## Test Data Files

### Resume Files

Prepare the following test resume files:

#### Valid Resume Files
1. **valid-resume-1.pdf** (2MB, standard format)
2. **valid-resume-2.pdf** (500KB, minimal format)
3. **valid-resume-3.pdf** (4.5MB, near size limit)

#### Invalid Resume Files (for negative testing)
1. **oversized-resume.pdf** (6MB, exceeds 5MB limit)
2. **invalid-format.docx** (Word document, not PDF)
3. **invalid-format.txt** (Text file, not PDF)

### Sample Job Data

#### Job Posting 1: Software Engineer
```
Title: Senior Software Engineer
Company: TechStart Inc
Location: San Francisco, CA
Remote: Yes
Job Type: Full-time
Experience Level: Senior
Description: We are seeking an experienced software engineer to join our growing team. You will work on cutting-edge technologies and help build scalable web applications.
Requirements:
- 5+ years of software development experience
- Strong knowledge of Python and JavaScript
- Experience with React and FastAPI
- Excellent problem-solving skills
Responsibilities:
- Design and implement new features
- Write clean, maintainable code
- Collaborate with cross-functional teams
- Mentor junior developers
Salary: $120,000 - $180,000
Currency: USD
Tags: python, javascript, react, fastapi, remote
```

#### Job Posting 2: Product Manager
```
Title: Product Manager
Company: GrowthCo LLC
Location: New York, NY
Remote: No
Job Type: Full-time
Experience Level: Mid
Description: Join our product team to drive the development of innovative solutions that delight our customers.
Requirements:
- 3+ years of product management experience
- Strong analytical skills
- Experience with Agile methodologies
- Excellent communication skills
Responsibilities:
- Define product roadmap
- Gather and prioritize requirements
- Work with engineering and design teams
- Analyze product metrics
Salary: $90,000 - $130,000
Currency: USD
Tags: product-management, agile, analytics
```

#### Job Posting 3: UX Designer
```
Title: UX Designer
Company: Enterprise Solutions Corp
Location: Austin, TX
Remote: Hybrid
Job Type: Full-time
Experience Level: Mid
Description: We're looking for a talented UX designer to create intuitive and beautiful user experiences.
Requirements:
- 3+ years of UX design experience
- Proficiency in Figma and Adobe Creative Suite
- Strong portfolio demonstrating UX process
- Understanding of accessibility standards
Responsibilities:
- Conduct user research
- Create wireframes and prototypes
- Design user interfaces
- Collaborate with developers
Salary: $80,000 - $120,000
Currency: USD
Tags: ux-design, figma, accessibility, user-research
```

---

## Test URLs for Import

### Valid Job URLs (Whitelisted Domains)

Use these sample URLs for testing URL import functionality:

```
LinkedIn:
https://www.linkedin.com/jobs/view/1234567890

Indeed:
https://www.indeed.com/viewjob?jk=abc123def456

Glassdoor:
https://www.glassdoor.com/job-listing/software-engineer-jv_id123456.htm
```

### Invalid URLs (for negative testing)

```
Non-whitelisted domain:
https://www.randomjobsite.com/job/12345

Invalid format:
not-a-valid-url

Missing protocol:
www.linkedin.com/jobs/view/1234567890
```

---

## Test Scenarios Setup

### Scenario 1: Job Seeker with Applications

**Setup Steps:**
1. Create testseeker2@example.com account
2. Login as testseeker2
3. Apply to 3-5 different jobs
4. Ensure applications have different statuses:
   - 2 applications: "Submitted"
   - 1 application: "Reviewed"
   - 1 application: "Shortlisted"
   - 1 application: "Rejected"

### Scenario 2: Employer with Active Jobs

**Setup Steps:**
1. Create employer-active@example.com account
2. Login as employer-active
3. Post 5 jobs with varying details:
   - 3 active jobs
   - 1 expired job
   - 1 filled job
4. Ensure at least 2 jobs have applications
5. Feature 1 job

### Scenario 3: Quota Testing

**Setup Steps:**
1. Login as employer-free@example.com
2. Post 3 jobs (reaching free tier limit)
3. Attempt to post 4th job (should fail)

### Scenario 4: Subscription Upgrade Flow

**Setup Steps:**
1. Create new employer account
2. Verify free tier (3 posts)
3. Post 3 jobs
4. Attempt 4th post (blocked)
5. Upgrade to Basic tier
6. Verify new limits (20 posts)

---

## Stripe Test Cards

Use these test card numbers for payment testing:

### Successful Payments
```
Card Number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

### Declined Payments
```
Card Number: 4000 0000 0000 0002
Expiry: Any future date
CVC: Any 3 digits
ZIP: Any 5 digits
```

### Requires Authentication (3D Secure)
```
Card Number: 4000 0025 0000 3155
Expiry: Any future date
CVC: Any 3 digits
ZIP: Any 5 digits
```

---

## Database Seeding Script

If you have access to the backend, you can use this script to seed test data:

```bash
# Navigate to backend directory
cd backend

# Run seeding script
python scripts/seed_test_data.py

# This will create:
# - 3 job seeker accounts
# - 4 employer accounts
# - 20 sample jobs
# - 10 sample applications
```

---

## Environment Variables

Ensure the following environment variables are set for testing:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/jobplatform_test
REDIS_URL=redis://localhost:6379/1
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

---

## Pre-Test Checklist

Before starting manual testing, verify:

- [ ] All test accounts are created
- [ ] Test resume files are prepared
- [ ] Sample job data is ready
- [ ] Test URLs are available
- [ ] Stripe test mode is enabled
- [ ] Database has seed data
- [ ] Frontend is running
- [ ] Backend is running
- [ ] Redis is running
- [ ] Celery workers are running

---

## Post-Test Cleanup

After testing is complete:

1. **Delete Test Accounts**
   - Remove all test job seeker accounts
   - Remove all test employer accounts

2. **Clean Test Data**
   - Delete test job postings
   - Delete test applications
   - Clear test files from storage

3. **Reset Quotas**
   - Reset monthly post counters
   - Reset featured post counters

4. **Database Cleanup**
   ```bash
   python scripts/cleanup_test_data.py
   ```

---

## Notes

- Always use test accounts, never production accounts
- Use Stripe test mode for payment testing
- Document any issues found during testing
- Take screenshots of bugs for reporting
- Keep test data organized and labeled clearly
