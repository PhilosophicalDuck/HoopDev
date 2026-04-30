import { useState } from 'react'
import { useUserStore } from '../stores/userStore'
import { updateProfile, type ProfileUpdate } from '../api/users'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'

const POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C']
const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced', 'elite']
const HANDS = ['right', 'left']
const GOAL_OPTIONS = [
  'shooting', 'ball_handling', 'footwork', 'conditioning',
  'defense', 'passing', 'rebounding', 'athleticism',
  'consistency', 'visualization',
]

export function Profile() {
  const { profile, setProfile } = useUserStore()
  const [form, setForm] = useState<ProfileUpdate>({
    position: profile?.position ?? '',
    skill_level: profile?.skill_level ?? '',
    dominant_hand: profile?.dominant_hand ?? '',
    height_cm: profile?.height_cm ?? undefined,
    weight_kg: profile?.weight_kg ?? undefined,
    goals: profile?.goals ?? [],
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  function update(field: keyof ProfileUpdate, value: unknown) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function toggleGoal(goal: string) {
    const current = form.goals ?? []
    update(
      'goals',
      current.includes(goal)
        ? current.filter((g) => g !== goal)
        : [...current, goal]
    )
  }

  async function handleSave() {
    setSaving(true)
    try {
      const updated = await updateProfile(form)
      setProfile(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout title="Profile">
      <div className="max-w-lg space-y-6">
        {/* Account info */}
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Account</h3>
          <p className="text-white font-medium">{profile?.user?.username}</p>
          <p className="text-gray-500 text-sm">{profile?.user?.email}</p>
        </div>

        {/* Position & Level */}
        <div className="bg-gray-900 rounded-xl p-4 space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Player Info</h3>

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
            <div className="flex gap-2 flex-wrap">
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
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Height (in)</label>
              <input
                type="number"
                value={form.height_cm ?? ''}
                onChange={(e) => update('height_cm', e.target.value ? parseFloat(e.target.value) : undefined)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Weight (lbs)</label>
              <input
                type="number"
                value={form.weight_kg ?? ''}
                onChange={(e) => update('weight_kg', e.target.value ? parseFloat(e.target.value) : undefined)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
              />
            </div>
          </div>
        </div>

        {/* Goals */}
        <div className="bg-gray-900 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Training Goals</h3>
          <div className="grid grid-cols-2 gap-2">
            {GOAL_OPTIONS.map((g) => (
              <button
                key={g}
                onClick={() => toggleGoal(g)}
                className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                  (form.goals ?? []).includes(g)
                    ? 'bg-orange-500/20 border border-orange-500 text-orange-400'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {g.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <Button loading={saving} onClick={handleSave} className="w-full justify-center">
          {saved ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>
    </Layout>
  )
}
