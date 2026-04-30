import cv2
import numpy as np
import pandas as pd

# ── Class constants ────────────────────────────────────────────────────────────
BALL_CLASS  = 0
HOOP_CLASS  = 2

SHOT_ZONE_W_FACTOR        = 3.5   # wider trigger zone — catches shots from angle
SHOT_ZONE_H_ABOVE         = 8.0   # look higher above rim for ball on the way up
SHOT_ZONE_H_BELOW         = 2.0   # look a bit further below rim too
COOLDOWN_FRAMES           = 45
RIM_RATIO                 = 0.3
MAX_LOST_FRAMES           = 15    # allow more frames without ball before abandoning
DEBUG_DRAW                = True
BALL_IN_BASKET_MIN_FRAMES = 1     # 2→1: ball only needs 1 frame in basket at 30fps
SHOT_DEADLINE_FRAMES      = 120   # 90→120: 4 s window (high-arc shots take longer)
MAX_BALL_MOVEMENT_PER_FRAME = 25
BASKET_X_MARGIN           = 0.3   # extend basket check zone by 30% of hoop width each side
# ──────────────────────────────────────────────────────────────────────────────


def box_center(xyxy):
    x1, y1, x2, y2 = xyxy
    return (x1 + x2) / 2, (y1 + y2) / 2


def best_detection(boxes, cls_id):
    """Return the highest-confidence box matching cls_id as [x1,y1,x2,y2], or None."""
    candidates = [b for b in boxes if int(b.cls[0]) == cls_id]
    if not candidates:
        return None
    best = max(candidates, key=lambda b: float(b.conf[0]))
    return best.xyxy[0].tolist()


def remove_wrong_detections(ball_positions):
    """
    Filter out ball detections that jump more than MAX_BALL_MOVEMENT_PER_FRAME
    pixels per frame gap — likely false positives.
    """
    last_good = -1
    for i in range(len(ball_positions)):
        cur_box = ball_positions[i].get(1, {}).get('bbox', [])
        if not cur_box:
            continue
        if last_good == -1:
            last_good = i
            continue
        last_box = ball_positions[last_good].get(1, {}).get('bbox', [])
        gap = i - last_good
        max_dist = MAX_BALL_MOVEMENT_PER_FRAME * gap
        if np.linalg.norm(np.array(last_box[:2]) - np.array(cur_box[:2])) > max_dist:
            ball_positions[i] = {}
        else:
            last_good = i
    return ball_positions


def interpolate_ball_positions(ball_positions):
    """Fill gaps in ball tracking using pandas linear interpolation + backfill."""
    raw = [x.get(1, {}).get('bbox', []) for x in ball_positions]
    df = pd.DataFrame(raw, columns=['x1', 'y1', 'x2', 'y2'])
    df = df.interpolate()
    df = df.bfill()
    return [{1: {"bbox": row}} for row in df.to_numpy().tolist()]


def draw_overlay(frame, shot_tracker, team_colors, count_a=0, count_b=0):
    """Draw a two-row HUD with team shot counts and player counts."""
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.65
    thickness  = 1
    color_a = team_colors.get("A", (128, 128, 128))
    color_b = team_colors.get("B", (128, 128, 128))
    made_a   = shot_tracker.made.get("A", 0)
    missed_a = shot_tracker.missed.get("A", 0)
    made_b   = shot_tracker.made.get("B", 0)
    missed_b = shot_tracker.missed.get("B", 0)
    label_a = f"Team A ({count_a}/5)   Made: {made_a}   Missed: {missed_a}"
    label_b = f"Team B ({count_b}/5)   Made: {made_b}   Missed: {missed_b}"
    (tw_a, th_a), _ = cv2.getTextSize(label_a, font, font_scale, thickness)
    (tw_b, th_b), _ = cv2.getTextSize(label_b, font, font_scale, thickness)
    pad     = 6
    sq      = 12
    row_h   = max(th_a, sq) + pad
    total_w = max(tw_a, tw_b) + sq + pad * 3
    total_h = row_h * 2 + pad
    cv2.rectangle(frame, (10, 10), (10 + total_w, 10 + total_h), (0, 0, 0), -1)
    for i, (label, color, th) in enumerate([
        (label_a, color_a, th_a),
        (label_b, color_b, th_b),
    ]):
        row_top = 10 + pad + i * row_h
        cv2.rectangle(frame,
                      (10 + pad, row_top),
                      (10 + pad + sq, row_top + sq),
                      color, -1)
        cv2.putText(frame, label,
                    (10 + pad + sq + pad, row_top + th),
                    font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


class ShotTracker:
    """
    Tracks shot attempts and outcomes using a ball position + hoop bounding box.
    State machine: IDLE → TRACKING → IDLE.
    """

    def __init__(self):
        self.state                      = "IDLE"
        self.cooldown                   = 0
        self.ball_was_above_rim         = False
        self.consecutive_ball_in_basket = 0
        self.shot_deadline_frame        = None
        self.lost_frames                = 0
        self.tracking_team              = "?"
        self.made                       = {"A": 0, "B": 0}
        self.missed                     = {"A": 0, "B": 0}

    def update(self, frame_idx, ball_bbox, hoop_bbox,
               possessing_team, last_known_possessing_team):
        """
        Process one frame of ball + hoop data.

        Returns:
            (event, team): event is 'MADE', 'MISS', or None; team is 'A', 'B', or '?'.
        """
        event = None
        event_team = "?"

        if self.cooldown > 0:
            self.cooldown -= 1

        if ball_bbox and hoop_bbox is not None:
            ball_cx, ball_cy = box_center(ball_bbox)
            hx1, hy1, hx2, hy2 = hoop_bbox
            hoop_cx = (hx1 + hx2) / 2
            hoop_w  = hx2 - hx1
            hoop_h  = hy2 - hy1
            rim_y   = hy1 + hoop_h * RIM_RATIO
            self.lost_frames = 0

            zone_x1 = hoop_cx - hoop_w * SHOT_ZONE_W_FACTOR / 2
            zone_x2 = hoop_cx + hoop_w * SHOT_ZONE_W_FACTOR / 2
            zone_y1 = rim_y   - hoop_h * SHOT_ZONE_H_ABOVE
            zone_y2 = rim_y   + hoop_h * SHOT_ZONE_H_BELOW
            in_zone = zone_x1 <= ball_cx <= zone_x2 and zone_y1 <= ball_cy <= zone_y2

            # Ball above rim — use a small grace band so slight detection lag
            # doesn't prevent this flag from being set
            if self.cooldown == 0 and ball_cy < rim_y + hoop_h * 0.5:
                self.ball_was_above_rim = True

            # Basket check — wider x margin to handle detection offset
            margin = hoop_w * BASKET_X_MARGIN
            ball_in_basket = (
                hx1 - margin <= ball_cx <= hx2 + margin
                and rim_y <= ball_cy <= rim_y + hoop_h * 2.0
            )
            self.consecutive_ball_in_basket = (
                self.consecutive_ball_in_basket + 1 if ball_in_basket else 0
            )

            if self.state == "IDLE" and in_zone and self.cooldown == 0:
                self.state = "TRACKING"
                self.tracking_team = (possessing_team if possessing_team != "?"
                                      else last_known_possessing_team)
                self.shot_deadline_frame        = frame_idx + SHOT_DEADLINE_FRAMES
                self.consecutive_ball_in_basket = 0

            if self.state == "TRACKING" and self.cooldown == 0:
                # Made shot
                if (self.ball_was_above_rim
                        and self.consecutive_ball_in_basket >= BALL_IN_BASKET_MIN_FRAMES):
                    event      = "MADE"
                    event_team = self.tracking_team
                    if self.tracking_team in self.made:
                        self.made[self.tracking_team] += 1
                    self._reset(cooldown=True)

                # Missed shot
                elif (self.shot_deadline_frame is not None
                      and frame_idx >= self.shot_deadline_frame):
                    if self.ball_was_above_rim:
                        event      = "MISS"
                        event_team = self.tracking_team
                        if self.tracking_team in self.missed:
                            self.missed[self.tracking_team] += 1
                        self.cooldown = COOLDOWN_FRAMES
                    self._reset(cooldown=False)

            # Store geometry for draw_debug
            self._last_hoop = hoop_bbox
            self._last_zone = (zone_x1, zone_y1, zone_x2, zone_y2)
            self._last_rim_y = rim_y

        elif self.state == "TRACKING":
            self.lost_frames += 1
            if self.lost_frames >= MAX_LOST_FRAMES:
                if self.ball_was_above_rim:
                    event      = "MISS"
                    event_team = self.tracking_team
                    if self.tracking_team in self.missed:
                        self.missed[self.tracking_team] += 1
                    self.cooldown = COOLDOWN_FRAMES
                self._reset(cooldown=False)

        return event, event_team

    def draw_debug(self, frame):
        """Draw shot zone and rim line if DEBUG_DRAW is enabled."""
        if not DEBUG_DRAW:
            return
        if not hasattr(self, '_last_hoop') or self._last_hoop is None:
            return
        hx1, hy1, hx2, hy2 = self._last_hoop
        zone_x1, zone_y1, zone_x2, zone_y2 = self._last_zone
        rim_y = self._last_rim_y
        zone_color = (0, 255, 255) if self.state == "TRACKING" else (100, 100, 100)
        cv2.rectangle(frame,
                      (int(zone_x1), int(zone_y1)),
                      (int(zone_x2), int(zone_y2)),
                      zone_color, 1)
        cv2.line(frame,
                 (int(hx1), int(rim_y)), (int(hx2), int(rim_y)),
                 (0, 0, 255), 2)

    def _reset(self, cooldown):
        self.tracking_team              = "?"
        self.ball_was_above_rim         = False
        self.consecutive_ball_in_basket = 0
        self.shot_deadline_frame        = None
        self.state                      = "IDLE"
        self.lost_frames                = 0
        if cooldown:
            self.cooldown = COOLDOWN_FRAMES
