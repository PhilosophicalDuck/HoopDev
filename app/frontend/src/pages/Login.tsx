import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { getProfile } from '../api/users'
import { useUserStore } from '../stores/userStore'
import { Button } from '../components/shared/Button'

export function Login() {
  const navigate = useNavigate()
  const { setToken, setProfile, enterDemo } = useUserStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { access_token } = await login({ email, password })
      setToken(access_token)
      const profile = await getProfile()
      setProfile(profile)
      navigate('/')
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-bold text-orange-400 text-center mb-1">HoopDev</h1>
        <p className="text-gray-500 text-center text-sm mb-8">AI Player Development</p>

        <div className="bg-gray-900 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-5">Sign in</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <Button type="submit" loading={loading} className="w-full justify-center">
              Sign in
            </Button>
          </form>

          <p className="text-gray-500 text-sm text-center mt-4">
            No account?{' '}
            <Link to="/register" className="text-orange-400 hover:text-orange-300">
              Register
            </Link>
          </p>
        </div>

        {/* Demo mode */}
        <div className="mt-4 text-center">
          <button
            onClick={() => { enterDemo(); navigate('/') }}
            className="text-sm text-gray-500 hover:text-orange-400 transition-colors"
          >
            Try Demo →
          </button>
          <p className="text-xs text-gray-700 mt-1">No account needed</p>
        </div>
      </div>
    </div>
  )
}
