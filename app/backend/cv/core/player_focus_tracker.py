import cv2
import numpy as np
from .player_tracker import get_jersey_features

class PlayerFocusTracker:
    def __init__(self, fps):
        self.fps = fps

        self.reference_features  = None   # HSV feature vector (click-based path)
        self.reference_gallery   = []     # HSV feature vectors (enrollment path)
        self.current_tracked_id  = -1     # track_id matched this frame

        self.touches   = 0
        self.made      = 0
        self.missed    = 0

    # ── Selection ──────────────────────────────────────────────────────────────

    def set_from_enrollment(self, gallery: list) -> bool:
        """
        Set the reference from an enrollment feature gallery.
        Uses nearest-neighbor matching across all gallery vectors.
        Returns False if gallery is empty.
        """
        if not gallery:
            return False
        self.reference_gallery = gallery
        return True

    def _feature_distance(self, feats) -> float:
        """
        Return the minimum L2 distance from feats to any vector in the gallery.
        Falls back to reference_features if the gallery is empty.
        """
        if self.reference_gallery:
            return float(min(
                np.linalg.norm(feats - ref) for ref in self.reference_gallery
            ))
        if self.reference_features is not None:
            return float(np.linalg.norm(feats - self.reference_features))
        return float('inf')

    def select_from_click(self, frame, player_tracks_frame):
        """Display frame, wait for click, extract reference jersey features."""
        display = frame.copy()
        for tid, info in player_tracks_frame.items():
            x1, y1, x2, y2 = [int(v) for v in info['bbox']]
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display, f"#{tid}", (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(display, "Click player to track | press any key to confirm",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

        clicked = [None]

        def _cb(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                clicked[0] = (x, y)

        try:
            cv2.namedWindow("Select Player to Track")
            cv2.setMouseCallback("Select Player to Track", _cb)
            while True:
                cv2.imshow("Select Player to Track", display)
                key = cv2.waitKey(50)
                if clicked[0] is not None or key != -1:
                    break
            cv2.destroyWindow("Select Player to Track")
        except cv2.error:
            print("  [focus tracker] No display available — skipping player selection.")
            return False

        if clicked[0] is None:
            return False   # user pressed key without clicking

        cx, cy = clicked[0]
        best_id, best_dist = -1, float('inf')
        for tid, info in player_tracks_frame.items():
            x1, y1, x2, y2 = info['bbox']
            d = (cx - (x1 + x2) / 2) ** 2 + (cy - (y1 + y2) / 2) ** 2
            if d < best_dist:
                best_dist, best_id = d, tid

        if best_id != -1:
            self.reference_features = get_jersey_features(
                frame, player_tracks_frame[best_id]['bbox'])
            self.current_tracked_id = best_id
            return True
        return False

    # ── Per-frame update ───────────────────────────────────────────────────────

    def update(self, frame, player_tracks_frame):
        """Re-identify tracked player by jersey features."""
        has_reference = self.reference_gallery or self.reference_features is not None
        if not has_reference or not player_tracks_frame:
            return

        best_id, best_dist = -1, float('inf')
        for tid, info in player_tracks_frame.items():
            feats = get_jersey_features(frame, info['bbox'])
            if feats is not None:
                d = self._feature_distance(feats)
                if d < best_dist:
                    best_dist, best_id = d, tid

        self.current_tracked_id = best_id

    def on_shot_event(self, event, possessing_id):
        """Call when shot_tracker fires an event."""
        if possessing_id == self.current_tracked_id:
            if event == "MADE":
                self.made += 1
            elif event == "MISS":
                self.missed += 1

    def update_touches(self, touch_counts):
        self.touches = touch_counts.get(self.current_tracked_id, 0)

    # ── Drawing ────────────────────────────────────────────────────────────────

    def highlight_player(self, frame, player_tracks_frame):
        """Draw a cyan highlight box around the tracked player."""
        if self.current_tracked_id == -1:
            return
        info = player_tracks_frame.get(self.current_tracked_id)
        if info is None:
            return
        x1, y1, x2, y2 = [int(v) for v in info['bbox']]
        cv2.rectangle(frame, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (0, 255, 255), 3)
        cv2.putText(frame, "TRACKED", (x1, y1 - 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

    def draw_overlay(self, frame):
        """Draw stats HUD in bottom-left corner."""
        if self.reference_features is None and not self.reference_gallery:
            return
        pid = self.current_tracked_id
        lines = [
            f"FOCUS  #{pid if pid != -1 else '?'}",
            f"Touch  {self.touches}",
            f"Shots  {self.made}M / {self.missed}Ms",
        ]
        font, fs, th = cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        lh, pad = 22, 8
        w = max(cv2.getTextSize(l, font, fs, th)[0][0] for l in lines) + pad * 2
        h = pad + len(lines) * lh + pad
        fh = frame.shape[0]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, fh - h), (w, fh), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        y = fh - h + pad + lh - 6
        for line in lines:
            color = (0, 255, 255) if line.startswith("FOCUS") else (255, 255, 255)
            cv2.putText(frame, line, (pad, y), font, fs, color, th, cv2.LINE_AA)
            y += lh
