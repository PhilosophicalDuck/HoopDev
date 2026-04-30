from pydantic_settings import BaseSettings
from pathlib import Path

# Root of the Capstone project (two levels up from this file)
CAPSTONE_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{CAPSTONE_ROOT}/basketball_app.db"
    secret_key: str = "change-this-to-a-random-secret-key-at-least-32-chars"
    access_token_expire_minutes: int = 10080  # 7 days
    camera_index: int = 0
    detection_model_path: str = str(CAPSTONE_ROOT / "models" / "best_yolos_player_detection.pt")
    hoop_model_path: str = str(CAPSTONE_ROOT / "models" / "best_yolo26s_player_detection.pt")
    pose_model_name: str = str(CAPSTONE_ROOT / "models" / "yolo11n-pose.pt")
    highlights_dir: str = str(CAPSTONE_ROOT / "highlights")
    max_upload_size_mb: int = 500
    algorithm: str = "HS256"
    mock_chat: bool = False

    model_config = {"env_file": str(CAPSTONE_ROOT / ".env"), "extra": "ignore"}


settings = Settings()


def model_paths_for_drill(drill_type: str) -> dict:
    """Return the model paths to activate for a given drill type.

    shooting             → hoop model on,  pose off
    ball_handling/footwork → hoop model off, pose on
    general/auto         → both on
    """
    shooting = drill_type == "shooting"
    dribbling = drill_type in ("ball_handling", "footwork")
    return {
        "detection_model_path": settings.detection_model_path,
        "hoop_model_path": settings.hoop_model_path if (shooting or not dribbling) else "",
        "pose_model_name": settings.pose_model_name if (dribbling or not shooting) else "",
    }
