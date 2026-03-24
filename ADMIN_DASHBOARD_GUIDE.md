# Admin Dashboard - User Guide

## Quick Start

1. **Login**: https://trusanity.com/login
   - Email: `admin@trusanity.com`
   - Password: `Admin@123`

2. **After Login**: You'll see admin navigation in the header:
   - Admin Dashboard
   - Users
   - Jobs

## Dashboard Overview

### Main Dashboard (`/admin/dashboard`)

The dashboard shows you everything at a glance:

#### Quick Stats (Top Row)
- **Total Users** 👥 - All users on the platform
- **Total Jobs** 💼 - All jobs posted (with active count)
- **Applications** 📝 - Total applications (with today's count)
- **Rate Limit Issues** ⚠️ - Users violating rate limits

#### User Breakdown
- Visual breakdown of Employers vs Job Seekers
- Percentage distribution
- Total counts

#### Today's Activity
- Jobs posted today
- Applications submitted today

#### Quick Actions
Three buttons to navigate to:
- Manage Users
- Monitor Jobs
- Rate Limits

## User Management (`/admin/users`)

View and manage all platform users:

### Features:
- **Search**: Find users by email or name
- **Filter by Role**: 
  - All Users
  - Admins
  - Employers
  - Job Seekers

### User Information Displayed:
- Email address
- Role (admin/employer/job_seeker)
- Join date
- Name or Company name

### Actions (Coming Soon):
- View user details
- Ban/unban users
- Delete users
- Send notifications

## Job Management (`/admin/jobs`)

Monitor all job postings on the platform:

### Planned Features:
- View all jobs
- Approve/reject jobs
- Flag inappropriate content
- Edit or remove jobs
- View job analytics

## Rate Limit Monitoring (`/admin/rate-limits`)

Track and manage API rate limit violations:

### Features:
- **Time Window Selector**: View violations from:
  - Last Hour
  - Last 24 Hours
  - Last Week

- **Overview Stats**:
  - Total violators
  - Time window

- **Top Violators**: See users with most violations

- **All Violators List**: Complete list with user IDs

### Actions:
- View violation details
- Clear violations for users

## Navigation

### Desktop Navigation
When logged in as admin, you'll see in the header:
- Home
- Search Jobs
- Admin Dashboard
- Users
- Jobs
- Logout

### Mobile Navigation
Tap the menu icon (☰) to see the same options in a mobile-friendly menu.

## Admin vs Employer vs Job Seeker

### What Makes Admin Different?

**Admin (You)**
- See EVERYTHING on the platform
- Manage all users
- Moderate all jobs
- View platform-wide analytics
- Control system settings
- Access: `/admin/*` routes

**Employer**
- See only their own data
- Post and manage their jobs
- View applications to their jobs
- Manage their subscription
- Access: `/employer/*` routes

**Job Seeker**
- Search and apply to jobs
- Manage their profile
- Track their applications
- Access: `/applications`, `/jobs/*` routes

## Security

- All admin pages check your role
- If you're not logged in as admin, you'll be redirected to login
- All backend API calls require admin authentication
- Your admin token is stored securely in the browser

## Tips

1. **Bookmark the Dashboard**: https://trusanity.com/admin/dashboard
2. **Check Daily**: Monitor today's activity stats
3. **Watch Rate Limits**: Keep an eye on violators
4. **User Management**: Use filters to find specific user types
5. **Mobile Friendly**: Access admin panel from your phone

## Troubleshooting

### Can't see admin navigation?
- Make sure you're logged in with admin@trusanity.com
- Check that login returned role: "admin"
- Try logging out and logging back in

### Dashboard not loading?
- Check your internet connection
- Try refreshing the page
- Check browser console for errors

### Statistics showing 0?
- This is normal if the platform is new
- Stats will update as users join and post jobs

## What's Coming Next

Future admin features:
- User ban/unban functionality
- Job approval workflow
- Advanced analytics with charts
- Email notification system
- Audit logs
- System settings panel
- Revenue tracking
- Export data functionality

## Support

If you need help or want to add new admin features, just ask!

---

**Remember**: You're the platform owner. You have full control over everything. Use this power wisely! 🚀
