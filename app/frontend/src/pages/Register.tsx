import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/auth'
import { useUserStore } from '../stores/userStore'
import { Button } from '../components/shared/Button'

export function Register() {
  const navigate = useNavigate()
  const { setToken } = useUserStore()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { access_token } = await register(form)
      setToken(access_token)
      navigate('/onboarding')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-bold text-orange-400 text-center mb-1">HoopDev</h1>
        <p className="text-gray-500 text-center text-sm mb-8">Create your account</p>

        <div className="bg-gray-900 rounded-2xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {(['username', 'email', 'password'] as const).map((field) => (
              <div key={field}>
                <label className="block text-sm text-gray-400 mb-1 capitalize">{field}</label>
                <input
                  type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
                  value={form[field]}
                  onChange={(e) => update(field, e.target.value)}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500"
                />
              </div>
            ))}

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <Button type="submit" loading={loading} className="w-full justify-center">
              Create account
            </Button>
          </form>

          <p className="text-gray-500 text-sm text-center mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-orange-400 hover:text-orange-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
