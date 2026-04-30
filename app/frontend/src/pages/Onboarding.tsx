import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { updateProfile } from '../api/users'
import { useUserStore } from '../stores/userStore'
import { Button } from '../components/shared/Button'

const POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C']
const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced', 'elite']
const HANDS = ['right', 'left']
const GOAL_OPTIONS = [
  'shooting', 'ball_handling', 'footwork', 'conditioning',
  'defense', 'passing', 'rebounding', 'athleticism',
  'consistency', 'visualization',
]

export function Onboarding() {
  const navigate = useNavigate()
  const { setProfile } = useUserStore()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    position: '',
    skill_level: '',
    dominant_hand: '',
    height_cm: '',
    weight_kg: '',
    goals: [] as string[],
  })

  function update(field: string, value: unknown) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function toggleGoal(goal: string) {
    setForm((prev) => ({
      ...prev,
      goals: prev.goals.includes(goal)
        ? prev.goals.filter((g) => g !== goal)
        : [...prev.goals, goal],
    }))
  }

  async function handleFinish() {
    setLoading(true)
    try {
      const updated = await updateProfile({
        position: form.position || undefined,
        skill_level: form.skill_level || undefined,
        dominant_hand: form.dominant_hand || undefined,
        height_cm: form.height_cm ? parseFloat(form.height_cm) : undefined,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : undefined,
        goals: form.goals.length > 0 ? form.goals : undefined,
      })
      setProfile(updated)
      navigate('/')
    } catch {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold text-white text-center mb-2">Set Up Your Profile</h1>
        <p className="text-gray-500 text-sm text-center mb-6">Step {step} of 3</p>

        {/* Progress bar */}
        <div className="flex gap-1 mb-8">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex-1 h-1 rounded-full ${s <= step ? 'bg-orange-500' : 'bg-gray-800'}`}
            />
          ))}
        </div>

        <div className="bg-gray-900 rounded-2xl p-6">
          {step === 1 && (
            <div className="space-y-5">
              <h2 className="font-semibold text-white">Position & Level</h2>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Position</label>
                <div className="flex gap-2 flex-wrap">
                  {POSITIONS.map((p) => (
                    <button
                      key={p}
                      onClick={() => update('position', p)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        form.position === p
                          ? 'bg-orange-500 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Skill Level</label>
                <div className="grid grid-cols-2 gap-2">
                  {SKILL_LEVELS.map((l) => (
                    <button
                      key={l}
                      onClick={() => update('skill_level', l)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                        form.skill_level === l
                          ? 'bg-orange-500 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Dominant Hand</label>
                <div className="flex gap-2">
                  {HANDS.map((h) => (
                    <button
                      key={h}
                      onClick={() => update('dominant_hand', h)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                        form.dominant_hand === h
                          ? 'bg-orange-500 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <h2 className="font-semibold text-white">Physical Info</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Height (in)</label>
                  <input
                    type="number"
                    value={form.height_cm}
                    onChange={(e) => update('height_cm', e.target.value)}
                    placeholder="e.g. 72"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Weight (lbs)</label>
                  <input
                    type="number"
                    value={form.weight_kg}
                    onChange={(e) => update('weight_kg', e.target.value)}
                    placeholder="e.g. 185"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-600">Optional — helps calibrate conditioning benchmarks.</p>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <h2 className="font-semibold text-white">Training Goals</h2>
              <p className="text-sm text-gray-500">Pick everything you want to improve.</p>
              <div className="grid grid-cols-2 gap-2">
                {GOAL_OPTIONS.map((g) => (
                  <button
                    key={g}
                    onClick={() => toggleGoal(g)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                      form.goals.includes(g)
                        ? 'bg-orange-500/20 border border-orange-500 text-orange-400'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {g.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-between mt-5">
          {step > 1 ? (
            <Button variant="ghost" onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => navigate('/')}>
              Skip
            </Button>
          )}

          {step < 3 ? (
            <Button onClick={() => setStep((s) => s + 1)}>Next</Button>
          ) : (
            <Button loading={loading} onClick={handleFinish}>
              Finish Setup
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
