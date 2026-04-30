import cv2


class HighlightWriter:
    """
    Records frame indices of made shots during Pass 2, then extracts and
    concatenates clips from the source video in a single post-processing pass.

    No frame buffer is held in memory — only a list of frame numbers.

    Usage:
        writer = HighlightWriter(...)

        # During Pass 2:
        if focus_player_scored:
            writer.on_made_shot(frame_idx)

        # After Pass 2:
        clips = writer.compile(source_video_path, total_frames)
    """

    def __init__(
        self,
        output_path: str,
        fps: float,
        pre_frames: int,
        post_frames: int,
    ) -> None:
        self._output_path = output_path
        self._fps         = fps
        self._pre_frames  = pre_frames
        self._post_frames = post_frames
        self._shot_frames: list[int] = []

    def on_made_shot(self, frame_idx: int) -> None:
        """Record that the focus player scored at frame_idx."""
        self._shot_frames.append(frame_idx)

    def compile(self, source_video_path: str, total_frames: int) -> int:
        """
        Seek to each recorded shot in the source video, extract a clip of
        (pre_frames + post_frames + 1) frames, and write all clips back-to-back
        into highlight_reel.avi.

        Args:
            source_video_path: Path to the original game video (not the annotated output).
            total_frames:      Total number of frames processed in Pass 2.

        Returns:
            Number of clips written. 0 means no output file was created.
        """
        if not self._shot_frames:
            return 0

        cap    = cv2.VideoCapture(source_video_path)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec  = "avc1" if self._output_path.lower().endswith(".mp4") else "XVID"
        writer = cv2.VideoWriter(
            self._output_path,
            cv2.VideoWriter_fourcc(*codec),
            self._fps,
            (width, height),
        )

        for shot_frame in self._shot_frames:
            start = max(0, shot_frame - self._pre_frames)
            end   = min(total_frames - 1, shot_frame + self._post_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            for _ in range(end - start + 1):
                ret, frame = cap.read()
                if not ret:
                    break
                writer.write(frame)

        cap.release()
        writer.release()
        return len(self._shot_frames)
