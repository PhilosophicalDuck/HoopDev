// All pre-built demo data for the live presentation demo mode.

export const DEMO_PROFILE = {
  user: { id: 1, username: 'Swish McKnight', email: 'demo@hoopddev.ai' },
  skill_level: 'intermediate',
  position: 'Guard',
  height_inches: 72,
  weight_lbs: 175,
  years_experience: 3,
}

export const DEMO_DASHBOARD = {
  total_sessions: 12,
  total_duration_minutes: 184,
  avg_shot_percentage: 0.67,
  recent_sessions: [
    {
      id: 1,
      drill_name: 'Free Throw Shooting',
      drill_type: 'shooting',
      duration_s: 510,
      created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      metrics: { shot_percentage: 0.91, shots_made: 10, shots_attempted: 11 },
    },
    {
      id: 2,
      drill_name: 'Dribble Combo Drill',
      drill_type: 'ball_handling',
      duration_s: 390,
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      metrics: { shot_percentage: null, shots_made: 0, shots_attempted: 0 },
    },
    {
      id: 3,
      drill_name: 'Mid-Range Shooting',
      drill_type: 'shooting',
      duration_s: 600,
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      metrics: { shot_percentage: 0.58, shots_made: 7, shots_attempted: 12 },
    },
  ],
}

export const DEMO_SESSION_DETAIL = {
  id: 1,
  drill_name: 'Free Throw Shooting',
  drill_type: 'shooting',
  duration_s: 510,
  source: 'video',
  created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  metrics: {
    shots_made: 10,
    shots_attempted: 11,
    shot_percentage: 0.91,
    avg_release_elbow_angle: null,
    avg_arc_angle_deg: 47.2,
    follow_through_ratio: 0.0,
    avg_speed_px_per_s: 269,
    top_speed_px_per_s: 1599,
    coaching_feedback_json: {
      strengths: [
        'High drill intensity — actively moving 100% of the session',
        'Excellent shooting accuracy at 91% field goal percentage',
        'Consistent arc angle averaging 47° — right in the target range',
      ],
      improvements: [
        'Incomplete follow-through',
      ],
      coaching_tips: {
        'Incomplete follow-through':
          'Hold the goose-neck follow-through for 2 full seconds after every release until it becomes automatic.',
      },
    },
  },
}

export const DEMO_WORKOUT_CATALOG = {
  drills: [
    {
      id: 'shooting',
      name: 'Shooting Drill',
      drill_type: 'shooting',
      description: 'Track shot arc, release consistency, and field goal percentage.',
      duration_minutes: 10,
      difficulty: 'intermediate',
    },
    {
      id: 'ball_handling',
      name: 'Dribbling / Ball Handling',
      drill_type: 'ball_handling',
      description: 'Analyze dribble rhythm, hand switches, and ball control.',
      duration_minutes: 10,
      difficulty: 'intermediate',
    },
  ],
}

export const DEMO_UPLOAD_RESULT = {
  session_id: 1,
  summary: {
    shots_made: 10,
    shots_attempted: 11,
    shot_percentage: 0.91,
    avg_release_elbow_angle: null,
    avg_arc_angle_deg: 47.2,
    follow_through_ratio: 0.0,
    avg_speed_px_per_s: 269,
    annotated_url: '/demo/annotated.mp4',
  },
  feedback: {
    strengths: [
      'High drill intensity — actively moving 100% of the session',
      'Excellent shooting accuracy at 91% field goal percentage',
      'Consistent arc angle averaging 47° — right in the target range',
    ],
    improvements: ['Incomplete follow-through'],
    coaching_tips: {
      'Incomplete follow-through':
        'Hold the goose-neck follow-through for 2 full seconds after every release until it becomes automatic.',
    },
  },
}

export const DEMO_FILM_ROOM_REPLIES: Record<string, Record<string, string>> = {
  sully: {
    release_angle: "47.2° is acceptable. You dropped below 42° on the last four shots — that's fatigue degrading your base. Fix your conditioning.",
    elbow_angle: "91° average. But you're flaring on the tail end. Inconsistent elbow position means inconsistent release. Lock it in every rep.",
    shot_arc: "Your arc is in range but it drifts low late in the session. Fatigue is your enemy here. Core strength and follow-through discipline.",
    fatigue: "That 52% drop-off in your last five shots tells me one thing — your conditioning is the ceiling on your game. Address it.",
    default: "The numbers don't lie. Study that chart, identify what broke down, and go fix it. Simple.",
  },
  buddy: {
    release_angle: "47.2° average?! That's right in the sweet spot — you're a sniper! The small dip at the end is just normal fatigue. I'm so proud of your consistency! 🔥",
    elbow_angle: "91° average — you're locked in for most of the session! A tiny bit of tightening on the late shots and your mechanics will be perfect!",
    shot_arc: "Your arc is looking beautiful! Staying in that 42-58° zone is exactly where the best shooters live. You've clearly been putting in the reps!",
    fatigue: "Hey, staying under 35% fatigue impact for most of the session is actually amazing! A little extra conditioning work and that tail-end dip disappears!",
    default: "You're out there doing the work and the data shows it! Keep trusting the process — every rep is making you better! 🔥",
  },
}

export const DEMO_CHAT_REPLIES: Record<string, string[]> = {
  sully: [
    "91% from the field is solid. But that follow-through needs to be automatic. Every. Single. Time.",
    "Discipline wins games, not talent. Your arc is in range — now lock in the release.",
    "I've seen the numbers. The fundamentals are there. Stop leaving points on the board with a lazy finish.",
    "A 47-degree arc is where we want it. Now make it consistent under pressure. That's the real test.",
  ],
  buddy: [
    "10 out of 11?! That's absolutely ELITE! You're putting in the work and it shows!",
    "Look at that arc — 47 degrees! You're dialed in today, keep riding that momentum!",
    "You're making serious progress every single session. I'm fired up watching these numbers climb!",
    "91% shooting?! Let's GOOO! A little more focus on the follow-through and you'll be unstoppable!",
  ],
}
