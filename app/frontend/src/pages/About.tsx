import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/shared/Layout'
import { useUserStore } from '../stores/userStore'


interface FeatureCard {
  icon: string
  title: string
  description: string
}

interface TechItem {
  label: string
  items: string[]
}

const CREATOR = {
  name: 'Logan Keiper',
  title: 'Author, Creator & Visionary',
  tagline: 'Advocate for every player who refuses to stop growing.',
  contributions: [
    { area: 'Computer Vision', detail: 'Custom YOLOv11 model — trained from scratch on 320+ hand-annotated basketball frames across 7 object classes' },
    { area: 'Backend', detail: 'FastAPI server, WebSocket real-time pipeline, SQLAlchemy data layer, and the full CV analysis stack' },
    { area: 'Shot Analysis', detail: 'Arc detection, elbow-angle tracking, follow-through recognition, and made/miss logic inside a per-frame pipeline' },
    { area: 'AI Coaching', detail: 'Feedback engine with debounced coaching cues and two Claude-powered AI personas — Sully and Buddy' },
    { area: 'Frontend', detail: 'React + TypeScript UI with live camera overlay, drill timer, skill radar, benchmark history, and highlight viewer' },
    { area: 'Dataset & Training', detail: 'Roboflow dataset management, Colab GPU training runs up to 250 epochs, dual-model architecture for speed vs. accuracy' },
  ],
}

const FEATURES: FeatureCard[] = [
  {
    icon: '📷',
    title: 'Live CV Analysis',
    description:
      'Real-time computer vision via webcam detects players, the ball, and the hoop frame-by-frame using a custom-trained YOLOv11 model.',
  },
  {
    icon: '🏀',
    title: 'Shot Tracking',
    description:
      'Automatic made/miss detection with arc angle, elbow angle, and follow-through analysis delivered to the player as instant coaching cues.',
  },
  {
    icon: '🤖',
    title: 'AI Coach Chat',
    description:
      'Two AI coaching personas — Sully (strict, results-driven) and Buddy (encouraging, motivational) — powered by the Claude API.',
  },
  {
    icon: '📊',
    title: 'Progress Dashboard',
    description:
      'Skill radar chart, benchmark history trend lines, and per-session metrics give players a data-driven view of improvement over time.',
  },
  {
    icon: '🎬',
    title: 'Highlight Clips',
    description:
      'The system automatically clips best-play moments from sessions and saves them so players can review, share, or export standout moments.',
  },
  {
    icon: '🎥',
    title: 'Video Upload',
    description:
      'Upload recorded game or practice footage for post-hoc analysis — the same CV pipeline runs offline and produces a full drill report.',
  },
  {
    icon: '🏋️',
    title: 'Workout Library',
    description:
      'A curated library of shooting, ball-handling, and footwork drills that feed directly into a guided live session with timed intervals.',
  },
  {
    icon: '📈',
    title: 'Benchmark System',
    description:
      'Track free-throw %, sprint times, dribble cadence, and more across weeks and months with persistent per-player benchmark history.',
  },
]

const TECH_STACK: TechItem[] = [
  {
    label: 'Computer Vision',
    items: ['YOLOv11 (Ultralytics)', 'OpenCV', 'MediaPipe (pose)', 'Custom dataset — 320+ annotated frames'],
  },
  {
    label: 'Backend',
    items: ['FastAPI (Python)', 'WebSockets (real-time feedback)', 'SQLAlchemy + SQLite', 'Anthropic Claude API'],
  },
  {
    label: 'Frontend',
    items: ['React 18 + TypeScript', 'Tailwind CSS', 'Recharts (data viz)', 'Zustand (state management)'],
  },
  {
    label: 'Training & Data',
    items: ['Roboflow (dataset management)', 'Google Colab (GPU training)', '7 object classes', '100–250 training epochs'],
  },
]

function StatBadge({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 text-center">
      <p className="text-3xl font-bold text-orange-400 font-mono">{value}</p>
      <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">{label}</p>
    </div>
  )
}

function FeatureCardView({ icon, title, description }: FeatureCard) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 space-y-2">
      <div className="text-2xl">{icon}</div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="text-xs text-gray-400 leading-relaxed">{description}</p>
    </div>
  )
}


function TechSection({ label, items }: TechItem) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-orange-400 uppercase tracking-wider">{label}</h4>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item} className="text-sm text-gray-300 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500 shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function About() {
  const token = useUserStore((s) => s.token)
  const { enterDemo } = useUserStore()
  const navigate = useNavigate()

  function handleDemo() {
    enterDemo()
    navigate('/')
  }

  const content = (
    <div className="max-w-5xl space-y-12">

        {/* Hero */}
        <div className="space-y-4">
          <h2 className="text-3xl font-bold text-white">
            AI-Powered Basketball{' '}
            <span className="text-orange-400">Player Development</span>
          </h2>
          <p className="text-gray-400 max-w-2xl leading-relaxed">
            HoopDev is a UNCG Computer Science Capstone project that brings professional-grade
            computer vision and AI coaching to individual basketball players. Using a custom-trained
            YOLOv11 detection model paired with a real-time feedback engine, the system watches a
            player's live camera feed and delivers instant coaching cues on shooting form, footwork,
            and ball handling — no coach required.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatBadge value="7" label="Object Classes" />
          <StatBadge value="320+" label="Annotated Frames" />
          <StatBadge value="250" label="Training Epochs" />
          <StatBadge value="2" label="AI Personas" />
        </div>

        {/* Model in Action */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-white">Model in Action</h3>
          <p className="text-sm text-gray-500">
            Real footage — annotated live by the YOLOv11 detection pipeline. Bounding boxes,
            class labels, and confidence scores are drawn frame-by-frame by the trained model.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="bg-gray-900 rounded-xl overflow-hidden">
                <video
                  src="/demo/shooting_h264.mp4"
                  controls
                  loop
                  className="w-full"
                  poster=""
                />
              </div>
              <div className="px-1">
                <p className="text-sm font-semibold text-white">Shooting Detection</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Player, ball, and hoop tracked in real time. Shot arc and elbow angle are
                  computed from bounding box positions each frame.
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="bg-gray-900 rounded-xl overflow-hidden">
                <video
                  src="/demo/dribbling_h264.mp4"
                  controls
                  loop
                  className="w-full"
                  poster=""
                />
              </div>
              <div className="px-1">
                <p className="text-sm font-semibold text-white">Dribbling & Ball Handling</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Ball possession, dribble rhythm, and hand-switch detection tracked across
                  frames using the same YOLOv11 model with pose estimation layered on top.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-white">Features</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f) => (
              <FeatureCardView key={f.title} {...f} />
            ))}
          </div>
        </section>

        {/* Tech Stack */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-white">Technology Stack</h3>
          <div className="bg-gray-900 rounded-xl p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {TECH_STACK.map((t) => (
                <TechSection key={t.label} {...t} />
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-white">How It Works</h3>
          <div className="bg-gray-900 rounded-xl p-6 space-y-6">
            {[
              {
                step: '01',
                title: 'Detection',
                body: 'Each camera frame is passed through a YOLOv11 model trained on 320+ annotated basketball images. The model identifies players, the ball, the hoop, referees, scoreboards, and overlays with high confidence.',
              },
              {
                step: '02',
                title: 'Tracking & Analysis',
                body: 'Detected bounding boxes are fed into a suite of trackers — ShotTracker for arc/made-miss logic, PoseAnalyzer for elbow and follow-through angles, and a TouchTracker for dribble rhythm. All run in a shared per-frame pipeline.',
              },
              {
                step: '03',
                title: 'Feedback Engine',
                body: 'The FeedbackEngine converts raw numeric frame data into debounced coaching cues with cooldown timers, preventing message spam. Cues are categorized by severity (info / warning / success) and topic (shooting / footwork / ball handling).',
              },
              {
                step: '04',
                title: 'Real-Time Delivery',
                body: 'Cues stream over WebSocket to the React frontend, where they appear as overlay badges on the live camera feed alongside a live metrics ticker showing shot %, elbow angle, and arc in real time.',
              },
              {
                step: '05',
                title: 'Post-Session Report',
                body: 'At session end, the system compiles a drill report with shot percentage, consistency score, and a highlight reel of best-play moments clipped automatically from the session recording.',
              },
            ].map(({ step, title, body }) => (
              <div key={step} className="flex gap-5">
                <div className="shrink-0 w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400 font-bold font-mono text-sm">
                  {step}
                </div>
                <div>
                  <p className="font-semibold text-white mb-1">{title}</p>
                  <p className="text-sm text-gray-400 leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Creator */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-white">The Creator</h3>
          <p className="text-sm text-gray-500">
            UNCG Computer Science &mdash; Senior Capstone &mdash; Spring 2026
          </p>
          <div className="bg-gray-900 rounded-xl p-6 space-y-6">
            {/* Identity */}
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 rounded-full bg-orange-500/20 border-2 border-orange-500/50 flex items-center justify-center text-orange-400 font-bold text-2xl shrink-0">
                L
              </div>
              <div>
                <p className="text-xl font-bold text-white">{CREATOR.name}</p>
                <p className="text-sm text-orange-400 font-medium">{CREATOR.title}</p>
                <p className="text-xs text-gray-500 mt-1 italic">{CREATOR.tagline}</p>
              </div>
            </div>

            {/* Contributions grid */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Built entirely solo — every line of code, every model weight, every design decision
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {CREATOR.contributions.map(({ area, detail }) => (
                  <div key={area} className="bg-gray-800/60 rounded-lg p-3 space-y-1">
                    <p className="text-xs font-semibold text-orange-400 uppercase tracking-wider">{area}</p>
                    <p className="text-xs text-gray-300 leading-relaxed">{detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Footer note */}
        <div className="border-t border-gray-800 pt-8 text-center">
          <p className="text-xs text-gray-600">
            HoopDev &mdash; UNCG Capstone &mdash; Spring 2026 &mdash; Built with React, FastAPI, YOLOv11 &amp; Claude
          </p>
        </div>

      </div>
  )

  // Authenticated: show inside the sidebar layout
  if (token) {
    return <Layout title="About HoopDev">{content}</Layout>
  }

  // Public landing: standalone page with top bar and CTA buttons
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Top bar */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <span className="text-xl font-bold text-orange-400">HoopDev</span>
          <span className="text-xs text-gray-500 ml-2">AI Player Development</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDemo}
            className="px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-400 text-white text-sm font-semibold transition-colors"
          >
            Try Demo
          </button>
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-white text-sm font-semibold transition-colors"
          >
            Sign In
          </button>
        </div>
      </header>

      {/* Page content */}
      <div className="p-8">
        {content}
      </div>
    </div>
  )
}
