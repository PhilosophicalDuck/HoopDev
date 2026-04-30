import cv2


class TouchTracker:
    def __init__(self):
        self.touch_counts = {}      # {track_id: int}
        self._last_possessor = -1   # last confirmed possessing track_id

    def update(self, possessing_id: int):
        """Call each frame with the confirmed possessing player ID (-1 = no one)."""
        if possessing_id != -1 and possessing_id != self._last_possessor:
            self.touch_counts[possessing_id] = self.touch_counts.get(possessing_id, 0) + 1
        self._last_possessor = possessing_id

    def get_counts(self) -> dict:
        return dict(self.touch_counts)

    def draw_overlay(self, frame, track_team_map=None, team_colors=None):
        """Draw a touch count panel in the top-left corner of frame."""
        if not self.touch_counts:
            return

        font       = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness  = 1
        line_h     = 22
        pad        = 8

        sorted_players = sorted(self.touch_counts.items(), key=lambda x: x[1], reverse=True)

        title      = "TOUCHES"
        title_size = cv2.getTextSize(title, font, font_scale, thickness)[0]
        max_w      = title_size[0]
        for pid, cnt in sorted_players:
            label     = f"P{pid}  {cnt}"
            text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
            max_w     = max(max_w, text_size[0] + line_h)  # leave room for color square

        panel_w = max_w + pad * 2 + 4
        panel_h = pad + line_h + pad // 2 + len(sorted_players) * line_h + pad

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Title
        cv2.putText(frame, title, (pad, pad + line_h - 6),
                    font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        y = pad + line_h + pad // 2
        for pid, cnt in sorted_players:
            # Team color square (12×12)
            color = (180, 180, 180)
            if track_team_map and team_colors:
                team = track_team_map.get(pid)
                if team and team in team_colors:
                    color = team_colors[team]
            sq_x1, sq_y1 = pad, y + 2
            sq_x2, sq_y2 = sq_x1 + 12, sq_y1 + 12
            cv2.rectangle(frame, (sq_x1, sq_y1), (sq_x2, sq_y2), color, -1)

            label = f"P{pid}  {cnt}"
            cv2.putText(frame, label, (pad + 16, y + line_h - 6),
                        font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
            y += line_h
