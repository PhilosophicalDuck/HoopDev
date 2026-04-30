from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Benchmark thresholds per skill level
# Keys match BenchmarkEntry.benchmark_type
THRESHOLDS: dict[str, dict[str, float]] = {
    "spot_shooting_pct": {
        "beginner": 40, "intermediate": 55, "advanced": 70, "elite": 80
    },
    "free_throw_streak": {
        "beginner": 5, "intermediate": 10, "advanced": 18, "elite": 25
    },
    "mikan_60s_makes": {
        "beginner": 12, "intermediate": 20, "advanced": 28, "elite": 35
    },
    "pull_up_20": {
        "beginner": 7, "intermediate": 10, "advanced": 13, "elite": 16
    },
    "sprint_17s": {  # lower is better
        "beginner": 85, "intermediate": 70, "advanced": 62, "elite": 58
    },
}

# Maps benchmark → drill category to focus on
BENCHMARK_TO_CATEGORY = {
    "spot_shooting_pct": "shooting",
    "free_throw_streak": "shooting",
    "mikan_60s_makes": "finishing",
    "pull_up_20": "shooting",
    "sprint_17s": "conditioning",
}

# Full drill catalog (mirrors routers/workouts.py DRILL_CATALOG — keep in sync)
DRILL_CATALOG = [
    # Shooting
    {"name": "Form Shots", "category": "shooting", "duration_min": 10, "cv_supported": True,
     "description": "One-foot, chest-to-basket shooting focused on wrist snap, guide-hand lift, and locked follow-through."},
    {"name": "5-Spot Circuit", "category": "shooting", "duration_min": 15, "cv_supported": True,
     "description": "Shoot from both corners, both wings, and the top of the key — 10 attempts per spot."},
    {"name": "Mikan Drill", "category": "finishing", "duration_min": 5, "cv_supported": True,
     "description": "Alternating layups off the backboard from both sides — trains soft touch and finishing rhythm. Target: 20+ makes in 60 seconds."},
    {"name": "Ray Allen Baseline", "category": "shooting", "duration_min": 10, "cv_supported": True,
     "description": "Curl from the corner to the elbow and fire a catch-and-shoot jumper, mirroring Ray Allen's off-screen movement."},
    {"name": "Kobe Mamba Method", "category": "shooting", "duration_min": 20, "cv_supported": True,
     "description": "High-volume spot shooting targeting 200+ makes per session. Conditions the shooting motion into muscle memory under fatigue."},
    # Ball Handling
    {"name": "Spider Dribble", "category": "ball_handling", "duration_min": 5, "cv_supported": True,
     "description": "Ball on the floor between feet — alternating hand taps front-to-back in a 'spider' pattern. Builds fingerpad sensitivity and low dribble quickness."},
    {"name": "Figure 8", "category": "ball_handling", "duration_min": 5, "cv_supported": True,
     "description": "Weave the ball in a figure-8 around both legs while staying low. Develops hip flexibility, core rotation, and quick hand transitions."},
    {"name": "Two-Ball Dribble", "category": "ball_handling", "duration_min": 8, "cv_supported": True,
     "description": "Simultaneously dribble two balls — same time, alternating, and staggered rhythms. Eliminates weak-hand dependency."},
    {"name": "Cone Weave", "category": "ball_handling", "duration_min": 10, "cv_supported": True,
     "description": "Dribble through 6 cones using crossover, between-legs, and behind-back moves at speed — eyes up throughout."},
    # Footwork
    {"name": "Pivot Work", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Triple-threat position pivot repetitions: front pivot and reverse pivot to create space and attack. Protects the ball from pressure defense."},
    {"name": "Jab Step Series", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Three-read triple-threat series: jab + shoot, jab + drive, jab + crossover. Fundamental to all perimeter scoring and shot creation."},
    {"name": "Defensive Slides", "category": "footwork", "duration_min": 10, "cv_supported": True,
     "description": "Lateral defensive shuffle in a low athletic stance — slide-step without crossing feet. The most fundamental on-ball defense technique in the game."},
    {"name": "Agility Ladder", "category": "footwork", "duration_min": 10, "cv_supported": False,
     "description": "Quick-feet ladder patterns: two-footed run, Ickey shuffle, lateral in-in-out-out, single-leg hops. Builds neuromuscular foot speed for change-of-direction."},
    {"name": "Closeout Technique", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Sprint from help position, chop your feet at 12 feet, raise the contest hand, and stay balanced. Prevents corner threes and forces drives into help defense."},
    {"name": "Drop Step Finish", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Back-to-the-basket drop step: feel the defender's hip, drop-step baseline or middle, power up into a layup or short hook. Essential low-post footwork."},
    # Conditioning
    {"name": "17s", "category": "conditioning", "duration_min": 10, "cv_supported": False,
     "description": "Sprint sideline to sideline 17 times in under 60 seconds — the standard NBA pre-season conditioning test. Develops anaerobic threshold and mental toughness."},
    {"name": "Full-Court Slides", "category": "conditioning", "duration_min": 8, "cv_supported": False,
     "description": "Defensive shuffle from baseline to baseline non-stop in a wide athletic stance. Builds hip abductor strength and the lateral conditioning to stay in front of ball-handlers all game."},
    {"name": "Jump Rope", "category": "conditioning", "duration_min": 5, "cv_supported": False,
     "description": "3-minute interval jump rope sets. Builds ankle stability, calf strength, rhythmic footwork, and overall conditioning. Add single-leg hops in the final minute."},
    {"name": "Suicide Sprints", "category": "conditioning", "duration_min": 8, "cv_supported": False,
     "description": "Sprint to the free-throw line and back, half-court and back, far free-throw line and back, far baseline and back — without stopping. Builds game-speed endurance for 4th-quarter performance."},
    {"name": "Wall Sits", "category": "conditioning", "duration_min": 5, "cv_supported": False,
     "description": "3 sets of 60-second wall sits at 90° knee bend. Builds the quad and glute endurance required for a consistent low defensive stance all game."},
    # Finishing
    {"name": "Euro Step Layup", "category": "finishing", "duration_min": 8, "cv_supported": True,
     "description": "Two-step lateral finish — plant the first foot, skip laterally, finish off the opposite hand. Popularized by Manu Ginobili and James Harden."},
    {"name": "Floater Series", "category": "finishing", "duration_min": 8, "cv_supported": True,
     "description": "High-arcing soft-touch finish over a shot-blocker in the lane — strong-hand and off-hand at 6, 10, and 14 feet. Tony Parker's primary mid-paint scoring tool."},
    {"name": "Reverse Layup", "category": "finishing", "duration_min": 6, "cv_supported": True,
     "description": "Drive baseline, finish on the opposite side of the backboard using the off-hand — the rim shields the ball from the defender."},
    # Visualization
    {"name": "Pre-Shot Routine", "category": "visualization", "duration_min": 8, "cv_supported": False,
     "description": "Build a consistent 3-step pre-shot sequence and rehearse it before every rep. Reduces choking under pressure by anchoring attention to process cues."},
    {"name": "Mental Rehearsal", "category": "visualization", "duration_min": 10, "cv_supported": False,
     "description": "Closed-eye visualization of perfect shot mechanics — see the arc, feel the release, hear the swish. Activates the same motor cortex patterns as physical reps."},
    {"name": "Positive Self-Talk", "category": "visualization", "duration_min": 5, "cv_supported": False,
     "description": "Replace negative cues ('don't miss') with process-focused phrases ('see it, shoot it'). Research shows instructional self-talk measurably improves shooting accuracy."},
    {"name": "Game Situation Replay", "category": "visualization", "duration_min": 12, "cv_supported": False,
     "description": "Mentally rehearse a full game sequence — read the defense, find the open man, make the decisive play. Builds basketball IQ and decision-making speed without physical fatigue."},
]


def _skill_level(profile) -> str:
    if profile and profile.skill_level:
        return profile.skill_level
    return "intermediate"


def _weakest_category(skill: str, benchmarks: dict[str, float]) -> str | None:
    """Return the drill category the user is furthest below their tier target."""
    worst_gap = 0.0
    worst_cat = None

    for btype, target_map in THRESHOLDS.items():
        target = target_map.get(skill, target_map["intermediate"])
        actual = benchmarks.get(btype)
        if actual is None:
            continue

        # For sprint_17s lower is better — invert the gap
        if btype == "sprint_17s":
            gap = (actual - target) / target  # positive = too slow
        else:
            gap = (target - actual) / target  # positive = below target

        if gap > worst_gap:
            worst_gap = gap
            worst_cat = BENCHMARK_TO_CATEGORY.get(btype)

    return worst_cat


def recommend(
    profile,
    recent_sessions: list,
    latest_benchmarks: dict[str, float],
    duration_min: int = 60,
    focus: str | None = None,
) -> dict:
    skill = _skill_level(profile)
    goals: list[str] = (profile.goals or []) if profile else []

    # Determine primary focus category
    primary = focus or _weakest_category(skill, latest_benchmarks) or "shooting"
    rationale = f"Focusing on {primary} — "
    if focus:
        rationale += "as requested."
    elif primary in latest_benchmarks or True:
        rationale += f"this is your weakest area relative to {skill} targets."

    # Build weighted pool: primary category gets 2 slots, others 1 each
    pool: list[dict] = []
    primary_drills = [d for d in DRILL_CATALOG if d["category"] == primary]
    other_drills = [d for d in DRILL_CATALOG if d["category"] != primary]

    # Add goal-relevant drills first, then fill with variety
    goal_categories = set(goals) | {primary}
    goal_drills = [d for d in other_drills if d["category"] in goal_categories]
    variety_drills = [d for d in other_drills if d["category"] not in goal_categories]

    # Build list with priority weighting
    ordered = primary_drills + goal_drills + variety_drills

    # Greedily fill up to duration_min, always include at least 1 primary drill
    selected: list[dict] = []
    total = 0
    seen_categories: set[str] = set()

    for drill in ordered:
        if total + drill["duration_min"] > duration_min:
            continue
        selected.append(drill)
        total += drill["duration_min"]
        seen_categories.add(drill["category"])
        if total >= duration_min - 5:
            break

    # Add conditioning if session ≥ 60 min and not already included
    if duration_min >= 60 and "conditioning" not in seen_categories:
        for d in DRILL_CATALOG:
            if d["category"] == "conditioning" and total + d["duration_min"] <= duration_min + 5:
                selected.append(d)
                total += d["duration_min"]
                break

    return {
        "recommended": selected,
        "total_duration_min": total,
        "rationale": rationale,
        "skill_level": skill,
        "primary_focus": primary,
    }
