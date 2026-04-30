"""
Thread-safe circular frame buffer for highlight capture.
Holds the last `capacity` raw BGR frames in memory.
When a MADE event fires, snapshot() returns the last N frames for clip writing.
"""
import threading
import numpy as np


class RingBuffer:
    def __init__(self, capacity: int = 150):
        """
        capacity: number of frames to keep.
                  150 = 5 seconds at 30 fps — enough for pre+post highlight window.
        """
        self._capacity = capacity
        self._buffer: list[np.ndarray] = []
        self._lock = threading.Lock()

    def push(self, frame: np.ndarray) -> None:
        with self._lock:
            self._buffer.append(frame)
            if len(self._buffer) > self._capacity:
                self._buffer.pop(0)

    def snapshot(self, n: int) -> list[np.ndarray]:
        """Return the last n frames (or all available if fewer exist)."""
        with self._lock:
            return list(self._buffer[-n:])

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)
