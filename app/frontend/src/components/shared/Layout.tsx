import { NavLink, useNavigate } from 'react-router-dom'
import { useUserStore } from '../../stores/userStore'
import { CoachChat } from './CoachChat'

interface LayoutProps {
  children: React.ReactNode
  title?: string
}

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/workouts', label: 'Workouts', icon: '🏋️' },
  { to: '/highlights', label: 'Highlights', icon: '🎬' },
  { to: '/film-room',  label: 'Stat Box',   icon: '📈' },
  { to: '/profile', label: 'Profile', icon: '👤' },
  { to: '/about', label: 'About', icon: 'ℹ️' },
]

export function Layout({ children, title }: LayoutProps) {
  const { profile, logout } = useUserStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
        <div className="p-5 border-b border-gray-800">
          <h1 className="text-lg font-bold text-orange-400">HoopDev</h1>
          <p className="text-xs text-gray-500 mt-0.5">AI Player Development</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-orange-500/20 text-orange-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-800">
          <div className="px-3 py-2 mb-1">
            <p className="text-sm font-medium text-white truncate">{profile?.user?.username ?? '—'}</p>
            <p className="text-xs text-gray-500 capitalize">{profile?.skill_level ?? 'Player'}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {title && (
          <header className="px-8 py-5 border-b border-gray-800">
            <h2 className="text-xl font-bold text-white">{title}</h2>
          </header>
        )}
        <div className="p-8">{children}</div>
      </main>

      <CoachChat />
    </div>
  )
}
