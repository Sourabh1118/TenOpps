#!/bin/bash

# Quick Fix for Admin Login - No Server Access Needed
# This creates the missing files locally, then you can deploy

set -e

echo "🔧 Quick Fix: Creating Missing Frontend Files..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Creating missing routes...${NC}"

# Create public directory if it doesn't exist
mkdir -p frontend/public

# Create grid.svg (decorative background pattern)
cat > frontend/public/grid.svg << 'EOF'
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="100" height="100" fill="url(#grid)" />
</svg>
EOF

echo -e "${GREEN}✓ Created grid.svg${NC}"

# Create employer/register redirect (it should go to /register/employer)
mkdir -p frontend/app/employer/register
cat > frontend/app/employer/register/page.tsx << 'EOF'
import { redirect } from 'next/navigation'

export default function EmployerRegisterRedirect() {
  redirect('/register/employer')
}
EOF

echo -e "${GREEN}✓ Created employer/register redirect${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Files Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📁 Created files:"
echo "   ✓ frontend/app/register/page.tsx"
echo "   ✓ frontend/app/employer/pricing/page.tsx"
echo "   ✓ frontend/app/employer/register/page.tsx"
echo "   ✓ frontend/public/grid.svg"
echo "   ✓ frontend/.env.production"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Commit the changes:"
echo "   git add ."
echo "   git commit -m 'Fix: Add missing routes and HTTPS config'"
echo "   git push origin main"
echo ""
echo "2. Deploy to server:"
echo "   ./FIX_FRONTEND_DEPLOYMENT.sh"
echo ""
echo "   OR manually:"
echo "   ssh -i trusanity-pem.pem ubuntu@3.110.220.37"
echo "   cd /home/jobplatform/job-platform"
echo "   sudo -u jobplatform git pull origin main"
echo "   cd frontend"
echo "   sudo -u jobplatform npm install"
echo "   sudo -u jobplatform npm run build"
echo "   sudo -u jobplatform pm2 restart job-platform-frontend"
echo ""
echo "3. Test admin login:"
echo "   URL: https://trusanity.com/login"
echo "   Email: admin@trusanity.com"
echo "   Password: Admin@123"
echo ""
echo "⚠️  IMPORTANT: Use HTTPS, not HTTP!"
echo ""
