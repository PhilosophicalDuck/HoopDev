"""
Core CV algorithm package.
All production-used modules are re-exported here for clean imports.
"""
from .shot_tracker import ShotTracker, best_detection, box_center
from .pose_analyzer import PoseAnalyzer
from .drill_metrics import DrillMetricsAccumulator, DrillMetricsSnapshot
from .drill_report import DrillReport, CoachingFeedback
from .player_tracker import PlayerTracker
from .player_focus_tracker import PlayerFocusTracker
from .touch_tracker import TouchTracker
from .highlight_writer import HighlightWriter
from .enrollment import run_enrollment

__all__ = [
    "ShotTracker", "best_detection", "box_center",
    "PoseAnalyzer",
    "DrillMetricsAccumulator", "DrillMetricsSnapshot",
    "DrillReport", "CoachingFeedback",
    "PlayerTracker", "PlayerFocusTracker",
    "TouchTracker", "HighlightWriter", "run_enrollment",
]
