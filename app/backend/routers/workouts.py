from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models.user import User
from app.backend.auth import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

# Drill catalog — sourced from basketball_solo_training_guide.md
DRILL_CATALOG = [
    # ── Shooting ──────────────────────────────────────────────────────────────
    {"name": "Form Shots", "category": "shooting", "duration_min": 10, "cv_supported": True,
     "description": "One-foot, chest-to-basket shooting with full focus on wrist snap, guide-hand lift, and locked follow-through. Used by Steph Curry and Kobe Bryant as the opening drill of every session to ingrain clean mechanics before adding distance."},
    {"name": "5-Spot Circuit", "category": "shooting", "duration_min": 15, "cv_supported": True,
     "description": "Shoot from both corners, both wings, and the top of the key — 10 attempts per spot. Track makes per spot to expose weak zones. Elite shooters target 60 %+ from all five positions."},
    {"name": "Mikan Drill", "category": "shooting", "duration_min": 5, "cv_supported": True,
     "description": "Alternating layups off the backboard from both sides — no dribble between makes. Named after Lakers legend George Mikan. Trains soft touch, footwork rhythm, and finishing in traffic. Target: 20+ makes in 60 seconds."},
    {"name": "Ray Allen Baseline", "category": "shooting", "duration_min": 10, "cv_supported": True,
     "description": "Curl from the corner to the elbow and fire a catch-and-shoot jumper, mirroring Ray Allen's off-screen movement. Builds shot-ready body position, quick release trigger, and footwork on catch."},
    {"name": "Kobe Mamba Method", "category": "shooting", "duration_min": 20, "cv_supported": True,
     "description": "High-volume spot shooting targeting 200+ makes per session across mid-range and 3-point zones. Kobe Bryant's documented pre-game routine — conditions the shooting motion into muscle memory and builds mental toughness under fatigue."},
    # ── Ball Handling ──────────────────────────────────────────────────────────
    {"name": "Spider Dribble", "category": "ball_handling", "duration_min": 5, "cv_supported": True,
     "description": "Ball on the floor between feet — alternating hand taps front-to-back in a 'spider' pattern. Builds fingerpad sensitivity, low dribble quickness, and the hand speed required for tight crossovers in live situations."},
    {"name": "Figure 8", "category": "ball_handling", "duration_min": 5, "cv_supported": True,
     "description": "Weave the ball in a figure-8 around both legs while staying low. Develops hip flexibility, core rotation, and quick hand transitions at waist level — directly translating to between-the-legs moves at speed."},
    {"name": "Two-Ball Dribble", "category": "ball_handling", "duration_min": 8, "cv_supported": True,
     "description": "Simultaneously dribble two balls — same time, alternating, and staggered rhythms. Used by NBA skill trainers to eliminate weak-hand dependency and build the rhythm needed for combo dribble moves."},
    {"name": "Cone Weave", "category": "ball_handling", "duration_min": 10, "cv_supported": True,
     "description": "Dribble through 6 cones using crossover, between-legs, and behind-back moves. Simulates live defender change-of-direction decisions at speed — keeps eyes up and head still throughout."},
    # ── Footwork ───────────────────────────────────────────────────────────────
    {"name": "Pivot Work", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Triple-threat position pivot repetitions: front pivot left and right, reverse pivot to create space, then attack. Used by elite wings to protect the ball from pressure, attack closeouts, and create passing angles without picking up the dribble."},
    {"name": "Jab Step Series", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Three-read triple-threat series: jab step + shoot (freeze the defender), jab step + drive (defender retreats), jab step + crossover (defender over-commits). Fundamental to all perimeter scoring and shot creation."},
    {"name": "Defensive Slides", "category": "footwork", "duration_min": 10, "cv_supported": True,
     "description": "Lateral defensive shuffle in a low athletic stance — chest to chest with the ball-handler, slide-step without crossing feet, push off the trail foot. The most fundamental on-ball defense technique in the game. Stay low, stay wide, mirror every move."},
    {"name": "Agility Ladder", "category": "footwork", "duration_min": 10, "cv_supported": False,
     "description": "Quick-feet ladder patterns: two-footed run, Ickey shuffle, lateral in-in-out-out, single-leg hops. Builds neuromuscular coordination and ground contact speed that transfer directly to change-of-direction on the court."},
    {"name": "Closeout Technique", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Sprint from help position, chop your feet at 12 feet, raise the high hand to contest, and stay balanced on the balls of your feet. The most important help-defense skill — prevents corner threes and forces drives into waiting help."},
    {"name": "Drop Step Finish", "category": "footwork", "duration_min": 8, "cv_supported": True,
     "description": "Back-to-the-basket footwork: catch the post entry pass, feel the defender's hip, drop-step baseline or middle, and power up into a layup or short hook. Essential low-post footwork used by every NBA big man from Hakeem to AD."},
    # ── Conditioning ──────────────────────────────────────────────────────────
    {"name": "17s", "category": "conditioning", "duration_min": 10, "cv_supported": False,
     "description": "Sprint sideline to sideline 17 times in under 60 seconds — the standard NBA pre-season conditioning test. Develops anaerobic threshold, mental toughness under fatigue, and the burst capacity needed for 4th-quarter defensive possessions. Rest 60 seconds between sets."},
    {"name": "Full-Court Slides", "category": "conditioning", "duration_min": 8, "cv_supported": False,
     "description": "Defensive shuffle from baseline to baseline without stopping, maintaining a wide athletic stance throughout. Builds hip abductor strength, lateral conditioning endurance, and the physical capacity to stay in front of ball-handlers for an entire game."},
    {"name": "Jump Rope", "category": "conditioning", "duration_min": 5, "cv_supported": False,
     "description": "3-minute interval jump rope sets with 30-second rest. Used by LeBron James, Steph Curry, and Kobe Bryant for ankle stability, calf strength, rhythmic footwork, and overall conditioning. Add single-leg hops in the final minute to increase difficulty."},
    {"name": "Suicide Sprints", "category": "conditioning", "duration_min": 8, "cv_supported": False,
     "description": "Sprint to the free-throw line and back, half-court and back, far free-throw line and back, far baseline and back — all without stopping. The classic basketball conditioning drill that builds the game-speed endurance and mental grit for late-game situations."},
    {"name": "Wall Sits", "category": "conditioning", "duration_min": 5, "cv_supported": False,
     "description": "3 sets of 60-second wall sits at 90° knee bend. Builds the quad and glute endurance required for a consistent low defensive stance all game. Used by strength coaches across the NBA as the baseline exercise for defensive conditioning programs."},
    # ── Finishing ─────────────────────────────────────────────────────────────
    {"name": "Euro Step Layup", "category": "finishing", "duration_min": 8, "cv_supported": True,
     "description": "Two-step lateral finish around a defender — plant the first foot, skip laterally, and finish off the opposite hand. Pioneered by Sarunas Marciulionis and popularized by Manu Ginobili and James Harden as one of the most unstoppable finishing moves in the game."},
    {"name": "Floater Series", "category": "finishing", "duration_min": 8, "cv_supported": True,
     "description": "High-arcing soft-touch finish over a shot-blocker in the lane — practice strong-hand and off-hand floaters at 6, 10, and 14 feet. Tony Parker and Steph Curry's primary mid-paint scoring tool when driving against rim protectors."},
    {"name": "Reverse Layup", "category": "finishing", "duration_min": 6, "cv_supported": True,
     "description": "Drive baseline and finish on the opposite side of the backboard using the off-hand — the rim becomes your shield against the defender. Essential counter move for guards and wings attacking closeouts from the corner."},
    # ── Visualization ─────────────────────────────────────────────────────────
    {"name": "Pre-Shot Routine", "category": "visualization", "duration_min": 8, "cv_supported": False,
     "description": "Build a consistent 3-step pre-shot sequence (breath, target, trigger word) and rehearse it before every rep. Research by Lidor & Singer (2003) shows pre-performance routines reduce choking under pressure by anchoring attention to process cues over outcome anxiety."},
    {"name": "Mental Rehearsal", "category": "visualization", "duration_min": 10, "cv_supported": False,
     "description": "Closed-eye visualization of perfect shot mechanics — see the arc, feel the fingertip release, hear the swish. NCAA and NBA research demonstrates that mental practice activates the same motor cortex firing patterns as physical repetitions."},
    {"name": "Positive Self-Talk", "category": "visualization", "duration_min": 5, "cv_supported": False,
     "description": "Replace negative internal cues ('don't miss') with process-focused instructional phrases ('see it, shoot it'). Research by Tod & Hardy (2009) shows instructional self-talk measurably improves shooting accuracy compared to motivational or no self-talk."},
    {"name": "Game Situation Replay", "category": "visualization", "duration_min": 12, "cv_supported": False,
     "description": "Mentally rehearse a full game sequence from start to finish — read the defense, find the open man, make the decisive pass or shot under pressure. Used by NBA coaches to build basketball IQ and decision-making speed without accumulating physical fatigue."},
]


@router.get("/recommend")
def recommend_workouts(
    duration_min: int = 60,
    focus: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.backend.services.workout_recommender import recommend
    from app.backend.models.session import DrillSession
    from app.backend.models.benchmark import BenchmarkEntry as BenchmarkModel

    profile = current_user.profile
    recent_sessions = (
        db.query(DrillSession)
        .filter(DrillSession.user_id == current_user.id, DrillSession.status == "completed")
        .order_by(DrillSession.started_at.desc())
        .limit(10)
        .all()
    )
    latest_benchmarks: dict[str, float] = {}
    for b in db.query(BenchmarkModel).filter(BenchmarkModel.user_id == current_user.id).all():
        if b.benchmark_type not in latest_benchmarks:
            latest_benchmarks[b.benchmark_type] = b.value

    return recommend(profile, recent_sessions, latest_benchmarks, duration_min, focus)


@router.get("/catalog")
def get_catalog():
    return {"drills": DRILL_CATALOG}
