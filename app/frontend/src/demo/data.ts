/**
 * Mock responses for every API endpoint used in the app.
 * Keyed by a simple "METHOD /path" pattern matched in adapter.ts.
 */

import type { UserProfile } from '../api/users'
import type { DashboardData } from '../api/dashboard'
import type { WorkoutPlan, DrillCard } from '../api/workouts'
import type { SessionDetail } from '../api/sessions'
import type { HighlightClipMeta } from '../api/highlights'

export const DEMO_PROFILE: UserProfile = {
  id: 1,
  user_id: 1,
  position: 'PG',
  skill_level: 'intermediate',
  height_cm: 72,
  weight_kg: 175,
  dominant_hand: 'right',
  goals: ['shooting', 'ball_handling', 'consistency'],
  updated_at: '2026-04-01T12:00:00Z',
  user: {
    id: 1,
    username: 'Swish McKnight',
    email: 'demo@hoopdev.app',
    created_at: '2026-01-15T08:00:00Z',
  },
}

export const DEMO_DASHBOARD: DashboardData = {
  radar: {
    shooting: 72,
    consistency: 65,
    ball_handling: 58,
    footwork: 70,
    conditioning: 63,
  },
  benchmark_history: {
    free_throw_pct: [
      { value: 52, recorded_at: '2026-02-01T00:00:00Z' },
      { value: 57, recorded_at: '2026-02-14T00:00:00Z' },
      { value: 61, recorded_at: '2026-03-01T00:00:00Z' },
      { value: 66, recorded_at: '2026-03-15T00:00:00Z' },
      { value: 72, recorded_at: '2026-04-01T00:00:00Z' },
    ],
    dribble_speed: [
      { value: 38, recorded_at: '2026-02-01T00:00:00Z' },
      { value: 41, recorded_at: '2026-02-14T00:00:00Z' },
      { value: 44, recorded_at: '2026-03-01T00:00:00Z' },
      { value: 47, recorded_at: '2026-03-15T00:00:00Z' },
      { value: 51, recorded_at: '2026-04-01T00:00:00Z' },
    ],
  },
  latest_benchmarks: {
    free_throw_pct: 72,
    dribble_speed: 51,
    sprint_10m_s: 1.84,
  },
  recent_sessions: [
    {
      id: 1,
      drill_name: 'Catch & Shoot',
      drill_type: 'shooting',
      started_at: '2026-04-14T10:30:00Z',
      duration_s: 1800,
      shot_percentage: 74,
      shots_made: 37,
      shots_attempted: 50,
    },
    {
      id: 2,
      drill_name: 'Ball Handling Circuit',
      drill_type: 'ball_handling',
      started_at: '2026-04-12T09:15:00Z',
      duration_s: 2400,
      shot_percentage: null,
    },
    {
      id: 3,
      drill_name: 'Free Throw Routine',
      drill_type: 'shooting',
      started_at: '2026-04-10T16:00:00Z',
      duration_s: 1200,
      shot_percentage: 68,
      shots_made: 17,
      shots_attempted: 25,
    },
    {
      id: 4,
      drill_name: 'Defensive Footwork',
      drill_type: 'footwork',
      started_at: '2026-04-08T11:00:00Z',
      duration_s: 1500,
      shot_percentage: null,
    },
    {
      id: 5,
      drill_name: 'Mid-Range Pull-Up',
      drill_type: 'shooting',
      started_at: '2026-04-06T14:30:00Z',
      duration_s: 1800,
      shot_percentage: 61,
      shots_made: 22,
      shots_attempted: 36,
    },
  ],
  total_sessions: 23,
}

const DEMO_DRILLS: DrillCard[] = [
  // ── Shooting ───────────────────────────────────────────────────────────────
  {
    name: 'Form Shots',
    category: 'shooting',
    duration_min: 10,
    cv_supported: true,
    description: 'One-foot, chest-to-basket shooting focused on wrist snap, guide-hand lift, and locked follow-through. Used by Steph Curry and Kobe Bryant as the opening drill of every session to ingrain clean mechanics before adding distance.',
  },
  {
    name: '5-Spot Circuit',
    category: 'shooting',
    duration_min: 15,
    cv_supported: true,
    description: 'Shoot from both corners, both wings, and the top of the key — 10 attempts per spot. Track makes per spot to expose weak zones. Elite shooters target 60%+ from all five positions.',
  },
  {
    name: 'Mikan Drill',
    category: 'shooting',
    duration_min: 5,
    cv_supported: true,
    description: 'Alternating layups off the backboard from both sides — no dribble between makes. Named after Lakers legend George Mikan. Trains soft touch, footwork rhythm, and finishing in traffic. Target: 20+ makes in 60 seconds.',
  },
  {
    name: 'Ray Allen Baseline',
    category: 'shooting',
    duration_min: 10,
    cv_supported: true,
    description: "Curl from the corner to the elbow and fire a catch-and-shoot jumper, mirroring Ray Allen's off-screen movement. Builds shot-ready body position, quick release trigger, and footwork on the catch.",
  },
  {
    name: 'Kobe Mamba Method',
    category: 'shooting',
    duration_min: 20,
    cv_supported: true,
    description: "High-volume spot shooting targeting 200+ makes per session across mid-range and 3-point zones. Kobe Bryant's documented pre-game routine — conditions the shooting motion into muscle memory and builds mental toughness under fatigue.",
  },
  // ── Ball Handling ──────────────────────────────────────────────────────────
  {
    name: 'Spider Dribble',
    category: 'ball_handling',
    duration_min: 5,
    cv_supported: true,
    description: "Ball on the floor between feet — alternating hand taps front-to-back in a 'spider' pattern. Builds fingerpad sensitivity, low dribble quickness, and the hand speed required for tight crossovers in live situations.",
  },
  {
    name: 'Figure 8',
    category: 'ball_handling',
    duration_min: 5,
    cv_supported: true,
    description: 'Weave the ball in a figure-8 around both legs while staying low. Develops hip flexibility, core rotation, and quick hand transitions at waist level — directly translating to between-the-legs moves at speed.',
  },
  {
    name: 'Two-Ball Dribble',
    category: 'ball_handling',
    duration_min: 8,
    cv_supported: true,
    description: 'Simultaneously dribble two balls — same time, alternating, and staggered rhythms. Used by NBA skill trainers to eliminate weak-hand dependency and build the rhythm needed for combo dribble moves.',
  },
  {
    name: 'Cone Weave',
    category: 'ball_handling',
    duration_min: 10,
    cv_supported: true,
    description: 'Dribble through 6 cones using crossover, between-legs, and behind-back moves. Simulates live defender change-of-direction decisions at speed — keeps eyes up and head still throughout.',
  },
  // ── Footwork ───────────────────────────────────────────────────────────────
  {
    name: 'Pivot Work',
    category: 'footwork',
    duration_min: 8,
    cv_supported: true,
    description: 'Triple-threat position pivot repetitions: front pivot left and right, reverse pivot to create space, then attack. Used by elite wings to protect the ball from pressure, attack closeouts, and create passing angles without picking up the dribble.',
  },
  {
    name: 'Jab Step Series',
    category: 'footwork',
    duration_min: 8,
    cv_supported: true,
    description: 'Three-read triple-threat series: jab step + shoot (freeze the defender), jab step + drive (defender retreats), jab step + crossover (defender over-commits). Fundamental to all perimeter scoring and shot creation.',
  },
  {
    name: 'Defensive Slides',
    category: 'footwork',
    duration_min: 10,
    cv_supported: true,
    description: 'Lateral defensive shuffle in a low athletic stance — chest to chest with the ball-handler, slide-step without crossing feet, push off the trail foot. The most fundamental on-ball defense technique in the game. Stay low, stay wide, mirror every move.',
  },
  {
    name: 'Agility Ladder',
    category: 'footwork',
    duration_min: 10,
    cv_supported: false,
    description: 'Quick-feet ladder patterns: two-footed run, Ickey shuffle, lateral in-in-out-out, single-leg hops. Builds neuromuscular coordination and ground contact speed that transfer directly to change-of-direction on the court.',
  },
  {
    name: 'Closeout Technique',
    category: 'footwork',
    duration_min: 8,
    cv_supported: true,
    description: 'Sprint from help position, chop your feet at 12 feet, raise the high hand to contest, and stay balanced on the balls of your feet. The most important help-defense skill — prevents corner threes and forces drives into waiting help.',
  },
  {
    name: 'Drop Step Finish',
    category: 'footwork',
    duration_min: 8,
    cv_supported: true,
    description: "Back-to-the-basket footwork: catch the post entry pass, feel the defender's hip, drop-step baseline or middle, and power up into a layup or short hook. Essential low-post footwork used by every NBA big man from Hakeem to AD.",
  },
  // ── Conditioning ──────────────────────────────────────────────────────────
  {
    name: '17s',
    category: 'conditioning',
    duration_min: 10,
    cv_supported: false,
    description: 'Sprint sideline to sideline 17 times in under 60 seconds — the standard NBA pre-season conditioning test. Develops anaerobic threshold, mental toughness under fatigue, and the burst capacity needed for 4th-quarter defensive possessions. Rest 60 seconds between sets.',
  },
  {
    name: 'Full-Court Slides',
    category: 'conditioning',
    duration_min: 8,
    cv_supported: false,
    description: 'Defensive shuffle from baseline to baseline without stopping, maintaining a wide athletic stance throughout. Builds hip abductor strength, lateral conditioning endurance, and the physical capacity to stay in front of ball-handlers for an entire game.',
  },
  {
    name: 'Jump Rope',
    category: 'conditioning',
    duration_min: 5,
    cv_supported: false,
    description: 'Three-minute interval jump rope sets with 30-second rest. Used by LeBron James, Steph Curry, and Kobe Bryant for ankle stability, calf strength, rhythmic footwork, and overall conditioning. Add single-leg hops in the final minute.',
  },
  {
    name: 'Suicide Sprints',
    category: 'conditioning',
    duration_min: 8,
    cv_supported: false,
    description: 'Sprint to the free-throw line and back, half-court and back, far free-throw line and back, far baseline and back — all without stopping. The classic basketball conditioning drill that builds the game-speed endurance and mental grit for late-game situations.',
  },
  {
    name: 'Wall Sits',
    category: 'conditioning',
    duration_min: 5,
    cv_supported: false,
    description: 'Three sets of 60-second wall sits at 90° knee bend. Builds the quad and glute endurance required for a consistent low defensive stance all game. Used by strength coaches across the NBA as the baseline exercise for defensive conditioning programs.',
  },
  // ── Finishing ─────────────────────────────────────────────────────────────
  {
    name: 'Euro Step Layup',
    category: 'finishing',
    duration_min: 8,
    cv_supported: true,
    description: 'Two-step lateral finish around a defender — plant the first foot, skip laterally, and finish off the opposite hand. Pioneered by Sarunas Marciulionis and popularized by Manu Ginobili and James Harden as one of the most unstoppable finishing moves in the game.',
  },
  {
    name: 'Floater Series',
    category: 'finishing',
    duration_min: 8,
    cv_supported: true,
    description: "High-arcing soft-touch finish over a shot-blocker in the lane — practice strong-hand and off-hand floaters at 6, 10, and 14 feet. Tony Parker and Steph Curry's primary mid-paint scoring tool when driving against rim protectors.",
  },
  {
    name: 'Reverse Layup',
    category: 'finishing',
    duration_min: 6,
    cv_supported: true,
    description: 'Drive baseline and finish on the opposite side of the backboard using the off-hand — the rim becomes your shield against the defender. Essential counter move for guards and wings attacking closeouts from the corner.',
  },
  // ── Visualization ─────────────────────────────────────────────────────────
  {
    name: 'Pre-Shot Routine',
    category: 'visualization',
    duration_min: 8,
    cv_supported: false,
    description: 'Build a consistent 3-step pre-shot sequence (breath, target, trigger word) and rehearse it before every rep. Research by Lidor & Singer (2003) shows pre-performance routines reduce choking under pressure by anchoring attention to process cues.',
  },
  {
    name: 'Mental Rehearsal',
    category: 'visualization',
    duration_min: 10,
    cv_supported: false,
    description: 'Closed-eye visualization of perfect shot mechanics — see the arc, feel the fingertip release, hear the swish. NCAA and NBA research demonstrates that mental practice activates the same motor cortex firing patterns as physical repetitions.',
  },
  {
    name: 'Positive Self-Talk',
    category: 'visualization',
    duration_min: 5,
    cv_supported: false,
    description: "Replace negative internal cues ('don't miss') with process-focused instructional phrases ('see it, shoot it'). Research by Tod & Hardy (2009) shows instructional self-talk measurably improves shooting accuracy.",
  },
  {
    name: 'Game Situation Replay',
    category: 'visualization',
    duration_min: 12,
    cv_supported: false,
    description: 'Mentally rehearse a full game sequence from start to finish — read the defense, find the open man, make the decisive pass or shot under pressure. Builds basketball IQ and decision-making speed without accumulating physical fatigue.',
  },
]

export const DEMO_CATALOG = { drills: DEMO_DRILLS }

export const DEMO_WORKOUT_PLAN: WorkoutPlan = {
  // Form Shots (10) + 5-Spot Circuit (15) + Two-Ball Dribble (8) + Defensive Slides (10) + Jump Rope (5) = 48 min
  recommended: [DEMO_DRILLS[0], DEMO_DRILLS[1], DEMO_DRILLS[7], DEMO_DRILLS[12], DEMO_DRILLS[17]],
  total_duration_min: 48,
  rationale:
    "Based on your recent sessions, your shooting consistency is improving — let's lock in the mechanics with Form Shots and the 5-Spot Circuit, sharpen your ball handling with Two-Ball Dribble, reinforce on-ball defense with Defensive Slides, and finish with a Jump Rope conditioning block.",
  skill_level: 'intermediate',
  primary_focus: 'shooting',
}

export const DEMO_SESSION: SessionDetail = {
  id: 1,
  drill_type: 'shooting',
  drill_name: 'Catch & Shoot',
  status: 'completed',
  started_at: '2026-04-14T10:30:00Z',
  ended_at: '2026-04-14T11:00:00Z',
  duration_s: 1800,
  shots_made: 37,
  shot_percentage: 74,
  highlights: [],
  metrics: {
    shots_made: 37,
    shots_attempted: 50,
    shot_percentage: 74,
    avg_release_elbow_angle: 88,
    avg_arc_angle_deg: 49,
    follow_through_ratio: 0.82,
    release_consistency_cv: 0.11,
    hand_switches: 0,
    dribble_rhythm_cv: undefined,
    avg_speed_px_per_s: 0,
    top_speed_px_per_s: 0,
    active_ratio: 0.91,
    coaching_feedback_json: {
      drill_type: 'shooting',
      strengths: [
        'Consistent elbow angle throughout the session (avg 88° — in the ideal 75–105° range)',
        'Strong follow-through on 82% of shots',
        'Good arc on most attempts — averaging 49°',
      ],
      improvements: [
        'A few rushed releases late in the session — focus on your pre-shot routine when fatigued',
        'Drift on catch-and-shoot reps from the left corner; square your hips earlier',
      ],
      coaching_tips: {
        elbow: 'Keep that elbow tucked — you\'re doing it well. Lock it in under pressure.',
        arc: 'Your arc is solid. On misses, check foot alignment before the catch.',
      },
    },
  },
}

export const DEMO_HIGHLIGHTS: HighlightClipMeta[] = []

export const DEMO_CHAT_REPLY = {
  sully: "Execute the follow-through every single time. That's not optional — that's the standard.",
  buddy: "You're out there putting in the work and that's everything! Keep that energy going!",
}

/** Location state passed to SessionReview when starting a drill in demo mode. */
export const DEMO_REVIEW_STATE = {
  summary: { shots_made: 37, shots_attempted: 50, shot_percentage: 74 },
  feedback: DEMO_SESSION.metrics!.coaching_feedback_json,
  highlight_clip_ids: [],
}
