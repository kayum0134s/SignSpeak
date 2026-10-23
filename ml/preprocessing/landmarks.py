"""
Landmark Feature Extraction using MediaPipe.
Extracts 3D coordinates for hands (21 left + 21 right = 42 landmarks)
plus upper body pose landmarks (shoulders, elbows, wrists = 6 landmarks).
Total feature dimension per frame: 48 landmarks * 3 (x, y, z) = 144 features.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np


FEATURE_DIM = 144  # 21 LH (63) + 21 RH (63) + 6 Pose (18)


class LandmarkExtractor:
    """
    Extracts spatial-temporal landmark feature sequences from video files or live frames.
    Includes caching to avoid redundant video processing.
    """

    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        import mediapipe as mp
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # lightweight for CPU speed
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def extract_frame_landmarks(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Extracts a 144-dimensional feature vector from a single BGR frame.
        Guaranteed to return shape (144,) float32 vector with zero-padding if hands not detected.
        """
        features = np.zeros(FEATURE_DIM, dtype=np.float32)
        if frame_bgr is None or frame_bgr.size == 0:
            return features

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # 1. Hand Landmarks: LH (0:63), RH (63:126)
        hand_results = self.hands.process(frame_rgb)
        if hand_results.multi_hand_landmarks and hand_results.multi_handedness:
            for hand_lms, handedness in zip(hand_results.multi_hand_landmarks, hand_results.multi_handedness):
                label = handedness.classification[0].label  # "Left" or "Right"
                offset = 0 if label == "Left" else 63
                coords = []
                for lm in hand_lms.landmark:
                    coords.extend([lm.x, lm.y, lm.z])
                features[offset:offset + 63] = np.array(coords, dtype=np.float32)

        # 2. Upper Pose Landmarks (126:144)
        # Landmark indices in MediaPipe Pose:
        # 11: left shoulder, 12: right shoulder, 13: left elbow, 14: right elbow, 15: left wrist, 16: right wrist
        pose_results = self.pose.process(frame_rgb)
        if pose_results.pose_landmarks:
            pose_lms = pose_results.pose_landmarks.landmark
            selected_indices = [11, 12, 13, 14, 15, 16]
            pose_coords = []
            for idx in selected_indices:
                if idx < len(pose_lms):
                    lm = pose_lms[idx]
                    pose_coords.extend([lm.x, lm.y, lm.z])
                else:
                    pose_coords.extend([0.0, 0.0, 0.0])
            features[126:144] = np.array(pose_coords, dtype=np.float32)

        return features

    def extract_video_landmarks(
        self,
        video_path: Union[str, Path],
        target_fps: Optional[float] = None,
        max_frames: Optional[int] = None,
        cache_dir: Optional[Path] = None
    ) -> np.ndarray:
        """
        Extracts landmark sequence from video file.
        Returns shape (T, 144) float32 numpy array.
        """
        vpath = Path(video_path)
        if cache_dir:
            cache_file = cache_dir / f"{vpath.stem}_landmarks.npy"
            if cache_file.exists():
                try:
                    return np.load(cache_file)
                except Exception:
                    pass

        cap = cv2.VideoCapture(str(vpath))
        if not cap.isOpened():
            # If video cannot be opened, return dummy 1-frame zero array
            return np.zeros((1, FEATURE_DIM), dtype=np.float32)

        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval = max(1, int(round(orig_fps / target_fps))) if target_fps else 1

        frame_list = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                lms = self.extract_frame_landmarks(frame)
                frame_list.append(lms)
                if max_frames and len(frame_list) >= max_frames:
                    break

            frame_idx += 1

        cap.release()

        if not frame_list:
            seq = np.zeros((1, FEATURE_DIM), dtype=np.float32)
        else:
            seq = np.stack(frame_list, axis=0)

        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            np.save(cache_dir / f"{vpath.stem}_landmarks.npy", seq)

        return seq

    def close(self):
        """Releases MediaPipe solution resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
        if hasattr(self, "pose") and self.pose:
            self.pose.close()
