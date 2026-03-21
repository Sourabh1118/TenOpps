import { ProtectedRoute } from '@/components/auth'
import { MainLayout } from '@/components/layout'

export default function TestProtectedPage() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold mb-4">Protected Page Test</h1>
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <p className="text-green-800 font-semibold mb-2">✓ Success!</p>
              <p className="text-green-700">
                If you can see this page, the ProtectedRoute component is working correctly.
                You are authenticated.
              </p>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-3">Test Instructions</h2>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                <li>If you&apos;re not logged in, you should have been redirected to /login</li>
                <li>If you are logged in, you should see this page</li>
                <li>Try logging out and accessing this page again</li>
                <li>You should be redirected to the login page</li>
              </ol>
            </div>
          </div>
        </div>
      </MainLayout>
    </ProtectedRoute>
  )
}
