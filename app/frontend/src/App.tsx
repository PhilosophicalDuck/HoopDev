import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useUserStore } from './stores/userStore'
import { Onboarding } from './pages/Onboarding'
import { Dashboard } from './pages/Dashboard'
import { WorkoutPicker } from './pages/WorkoutPicker'
import { LiveSession } from './pages/LiveSession'
import { SessionReview } from './pages/SessionReview'
import { Highlights } from './pages/Highlights'
import { Profile } from './pages/Profile'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { VideoUpload } from './pages/VideoUpload'
import { About } from './pages/About'
import { FilmRoom } from './pages/FilmRoom'
import { DemoLiveSession } from './pages/DemoLiveSession'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useUserStore((s) => s.token)
  if (!token) return <Navigate to="/about" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          path="/workouts"
          element={
            <RequireAuth>
              <WorkoutPicker />
            </RequireAuth>
          }
        />
        <Route
          path="/session/:sessionId"
          element={
            <RequireAuth>
              <LiveSession />
            </RequireAuth>
          }
        />
        <Route
          path="/review/:sessionId"
          element={
            <RequireAuth>
              <SessionReview />
            </RequireAuth>
          }
        />
        <Route
          path="/highlights"
          element={
            <RequireAuth>
              <Highlights />
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/upload"
          element={
            <RequireAuth>
              <VideoUpload />
            </RequireAuth>
          }
        />
        <Route
          path="/film-room"
          element={
            <RequireAuth>
              <FilmRoom />
            </RequireAuth>
          }
        />
        <Route path="/session/demo" element={<DemoLiveSession />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<Navigate to="/about" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
