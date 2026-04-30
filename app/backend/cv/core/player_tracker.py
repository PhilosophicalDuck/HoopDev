import cv2
import math
import numpy as np
from sklearn.cluster import KMeans
import supervision as sv

# ── Config ────────────────────────────────────────────────────────────────────
PLAYER_CLASS          = 4
CALIB_FRAMES          = 60   # frames to collect jersey samples before KMeans
POSSESSION_MIN_FRAMES = 11   # consecutive frames required to confirm possession
POSSESSION_THRESHOLD  = 50   # max px from ball edge to count as possession
CONTAINMENT_THRESHOLD = 0.8  # ball containment ratio → auto-confirm possession
# ──────────────────────────────────────────────────────────────────────────────


# ── Jersey / team helpers ─────────────────────────────────────────────────────

def get_jersey_features(frame, xyxy):
    """
    Extract HSV colour features from the torso region of a player bounding box.
    Returns [H_mean, H_std, S_mean, S_std, V_mean, V_std] or None.
    """
    x1, y1, x2, y2 = [int(v) for v in xyxy]
    box_w = x2 - x1
    box_h = y2 - y1
    tx1 = x1 + int(box_w * 0.20)
    tx2 = x1 + int(box_w * 0.80)
    ty1 = y1 + int(box_h * 0.10)
    ty2 = y1 + int(box_h * 0.50)
    if (tx2 - tx1) < 20 or (ty2 - ty1) < 20:
        return None
    crop = frame[ty1:ty2, tx1:tx2]
    if crop.size == 0:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).astype(np.float32)
    h = hsv[:, :, 0].ravel()
    s = hsv[:, :, 1].ravel()
    v = hsv[:, :, 2].ravel()
    return np.array([h.mean(), h.std(), s.mean(), s.std(), v.mean(), v.std()],
                    dtype=np.float32)


def centroid_to_bgr(centroid):
    """Convert a KMeans centroid [H_mean, _, S_mean, _, V_mean, _] to a BGR colour."""
    h, s, v = float(centroid[0]), float(centroid[2]), float(centroid[4])
    hsv_pixel = np.array([[[h, s, v]]], dtype=np.uint8)
    bgr = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)
    return (int(bgr[0, 0, 0]), int(bgr[0, 0, 1]), int(bgr[0, 0, 2]))


# ── Possession detection helpers ──────────────────────────────────────────────

def _measure_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_key_possession_points(player_bbox, ball_center):
    """
    Return key points around the player bbox for distance-to-ball measurement.
    Prioritises points on the same row/column as the ball.
    """
    ball_cx, ball_cy = ball_center
    x1, y1, x2, y2 = player_bbox
    w = x2 - x1
    h = y2 - y1

    pts = []
    if y1 < ball_cy < y2:
        pts += [(x1, ball_cy), (x2, ball_cy)]
    if x1 < ball_cx < x2:
        pts += [(ball_cx, y1), (ball_cx, y2)]

    pts += [
        (x1 + w // 2, y1),
        (x2, y1),
        (x1, y1),
        (x2, y1 + h // 2),
        (x1, y1 + h // 2),
        (x1 + w // 2, y1 + h // 2),
        (x2, y2),
        (x1, y2),
        (x1 + w // 2, y2),
        (x1 + w // 2, y1 + h // 3),
    ]
    return pts


def calculate_containment_ratio(player_bbox, ball_bbox):
    """Fraction of the ball's bbox area that overlaps the player's bbox."""
    px1, py1, px2, py2 = player_bbox
    bx1, by1, bx2, by2 = ball_bbox
    ix1, iy1 = max(px1, bx1), max(py1, by1)
    ix2, iy2 = min(px2, bx2), min(py2, by2)
    if ix2 < ix1 or iy2 < iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    ball_area = (bx2 - bx1) * (by2 - by1)
    return intersection / ball_area if ball_area > 0 else 0.0


def find_best_possession_candidate(ball_center, ball_bbox, player_tracks_frame):
    """
    Return the track_id of the player most likely holding the ball, or -1.

    Priority:
      1. Player whose bbox contains >CONTAINMENT_THRESHOLD of the ball bbox.
      2. Player closest to the ball (by key-point distance) within POSSESSION_THRESHOLD.
    """
    high_containment = []
    regular = []

    for track_id, info in player_tracks_frame.items():
        player_bbox = info.get('bbox', [])
        if not player_bbox:
            continue
        containment = calculate_containment_ratio(player_bbox, ball_bbox)
        key_pts = get_key_possession_points(player_bbox, ball_center)
        min_dist = min(_measure_distance(ball_center, pt) for pt in key_pts)

        if containment > CONTAINMENT_THRESHOLD:
            high_containment.append((track_id, min_dist))
        else:
            regular.append((track_id, min_dist))

    if high_containment:
        return min(high_containment, key=lambda x: x[1])[0]
    if regular:
        best = min(regular, key=lambda x: x[1])
        if best[1] < POSSESSION_THRESHOLD:
            return best[0]
    return -1


# ── Drawing ───────────────────────────────────────────────────────────────────

def draw_player_labels(frame, player_tracks_frame, track_team_map, team_colors):
    """
    Draw a team badge and track ID on each tracked player.
    Returns (count_a, count_b).
    """
    count_a = count_b = 0
    for track_id, info in player_tracks_frame.items():
        team  = track_team_map.get(track_id, "?")
        color = team_colors.get(team, (128, 128, 128))
        if team == "A":
            count_a += 1
        elif team == "B":
            count_b += 1
        bbox = info['bbox']
        x1, y1 = int(bbox[0]), int(bbox[1])
        bw, bh = 18, 16
        cv2.rectangle(frame, (x1, y1), (x1 + bw, y1 + bh), color, -1)
        cv2.putText(frame, team, (x1 + 3, y1 + bh - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"#{track_id}", (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1, cv2.LINE_AA)
    return count_a, count_b


# ── PlayerTracker class ───────────────────────────────────────────────────────

class PlayerTracker:
    """
    Handles player detection, ByteTrack ID assignment, jersey-colour calibration,
    team assignment, and possession detection.
    """

    def __init__(self):
        self.tracker       = sv.ByteTrack()
        self.calib_ready   = False
        self.calib_km      = None
        self.calib_mapping = {}   # {cluster_int: "A" | "B"}
        self.team_colors   = {}   # {"A": (B,G,R), "B": (B,G,R)}
        self.track_team_map = {}  # {track_id: "A" | "B"}

        # Possession state
        self.possessing_team            = "?"
        self.last_known_possessing_team = "?"
        self.possessing_id              = -1   # track_id of confirmed possessing player
        self._consecutive_possession    = {}  # {track_id: frame_count}

    # ── ByteTrack ─────────────────────────────────────────────────────────────

    def run_bytetrack(self, raw_player_dets):
        """
        Run ByteTrack over all frames' raw player detections.

        Args:
            raw_player_dets: list of [{"bbox": [...], "conf": float}] per frame.

        Returns:
            player_tracks: list of {track_id: {"bbox": [x1,y1,x2,y2]}} per frame.
        """
        player_tracks = []
        for players in raw_player_dets:
            if players:
                xyxy    = np.array([p["bbox"] for p in players], dtype=np.float32)
                confs   = np.array([p["conf"] for p in players], dtype=np.float32)
                cls_ids = np.zeros(len(players), dtype=int)
                det_sv  = sv.Detections(xyxy=xyxy, confidence=confs, class_id=cls_ids)
            else:
                det_sv = sv.Detections(xyxy=np.empty((0, 4), dtype=np.float32), confidence=np.empty(0, dtype=np.float32))

            tracked = self.tracker.update_with_detections(det_sv)
            frame_tracks = {}
            if tracked.tracker_id is not None:
                for i in range(len(tracked)):
                    frame_tracks[int(tracked.tracker_id[i])] = {
                        "bbox": tracked.xyxy[i].tolist()
                    }
            player_tracks.append(frame_tracks)
        return player_tracks

    # ── Calibration ───────────────────────────────────────────────────────────

    def run_calibration(self, calib_samples):
        """
        Fit KMeans on jersey feature samples to separate the two teams.

        Args:
            calib_samples: list of feature vectors from get_jersey_features().
        """
        if len(calib_samples) < 4:
            print("  Not enough player samples for calibration — team labels disabled.")
            return

        km = KMeans(n_clusters=2, n_init=10, random_state=0)
        km.fit(np.array(calib_samples))

        c0_hue, c1_hue = km.cluster_centers_[0][0], km.cluster_centers_[1][0]
        self.calib_mapping = {0: "A", 1: "B"} if c0_hue <= c1_hue else {0: "B", 1: "A"}
        self.team_colors   = {
            self.calib_mapping[0]: centroid_to_bgr(km.cluster_centers_[0]),
            self.calib_mapping[1]: centroid_to_bgr(km.cluster_centers_[1]),
        }
        sep = abs(c0_hue - c1_hue)
        if sep < 5.0:
            print(f"  Warning: jersey hue separation only {sep:.1f} — may be unreliable.")

        self.calib_km    = km
        self.calib_ready = True

        a_cl   = next(k for k, v in self.calib_mapping.items() if v == "A")
        b_cl   = 1 - a_cl
        counts = np.bincount(km.labels_, minlength=2)
        print(f"  Calibration done. Team A hue≈{km.cluster_centers_[a_cl][0]:.1f}, "
              f"sep={sep:.1f}")
        print(f"  Cluster sizes — A: {counts[a_cl]}, B: {counts[b_cl]} "
              f"(total {len(calib_samples)} samples)")
        balance = min(counts) / max(counts) if max(counts) > 0 else 0
        if balance < 0.4:
            print(f"  Warning: unbalanced clusters ({balance:.2f}) — "
                  "team assignment may be unreliable.")

    # ── Team assignment ───────────────────────────────────────────────────────

    def assign_team(self, frame, track_id, bbox):
        """
        Assign a team to a track_id if not already cached.
        Uses jersey features + KMeans prediction.
        """
        if not self.calib_ready or track_id in self.track_team_map:
            return
        feats = get_jersey_features(frame, bbox)
        if feats is not None:
            cluster = int(self.calib_km.predict(feats.reshape(1, -1))[0])
            self.track_team_map[track_id] = self.calib_mapping.get(cluster, "?")

    def get_team(self, track_id):
        """Return the team label for a track_id, or '?'."""
        return self.track_team_map.get(track_id, "?")

    # ── Possession ────────────────────────────────────────────────────────────

    def update_possession(self, ball_center, ball_bbox, player_tracks_frame):
        """
        Update possession state for the current frame.
        Requires POSSESSION_MIN_FRAMES consecutive frames before confirming.
        """
        if not self.calib_ready:
            return

        best_id = find_best_possession_candidate(
            ball_center, ball_bbox, player_tracks_frame
        )

        if best_id != -1:
            n = self._consecutive_possession.get(best_id, 0) + 1
            self._consecutive_possession = {best_id: n}
            if n >= POSSESSION_MIN_FRAMES:
                team = self.track_team_map.get(best_id, "?")
                self.possessing_team = team
                self.possessing_id = best_id
                if team != "?":
                    self.last_known_possessing_team = team
        else:
            self._consecutive_possession = {}

    def draw_labels(self, frame, player_tracks_frame):
        """Draw team badges on all tracked players. Returns (count_a, count_b)."""
        return draw_player_labels(
            frame, player_tracks_frame, self.track_team_map, self.team_colors
        )
