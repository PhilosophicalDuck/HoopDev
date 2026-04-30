"""
Manages a single cv2.VideoCapture instance for the live session.
Opened once when a session starts, released when it ends.

Thread-safe: read_frame() can be called from the CV worker thread and
the MJPEG streaming thread simultaneously without conflict.
"""
import logging
import threading
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._index: int = 0
        self._lock = threading.Lock()

    def open(self, device_index: int = 0) -> bool:
        with self._lock:
            if self._cap and self._cap.isOpened():
                self._cap.release()
            self._index = device_index
            self._cap = cv2.VideoCapture(device_index)
            if not self._cap.isOpened():
                logger.error("Failed to open camera index %d", device_index)
                self._cap = None
                return False
        logger.info("Camera %d opened (%.0f fps, %dx%d)",
                    device_index, self.get_fps(), *self.get_resolution())
        return True

    def close(self) -> None:
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
                logger.info("Camera %d closed", self._index)

    def read_frame(self) -> np.ndarray | None:
        with self._lock:
            if not self._cap or not self._cap.isOpened():
                return None
            ret, frame = self._cap.read()
            return frame if ret else None

    def get_fps(self) -> float:
        if not self._cap:
            return 30.0
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        return fps if fps > 0 else 30.0

    def get_resolution(self) -> tuple[int, int]:
        if not self._cap:
            return (640, 480)
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (w, h)

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()


# Module-level singleton shared between MJPEG stream and LivePipeline
camera = CameraManager()
