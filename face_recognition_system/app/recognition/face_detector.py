"""
face_detector.py — Detección facial con YuNet (cv2.FaceDetectorYN).
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path

from config import YUNET_MODEL, FRAME_WIDTH, FRAME_HEIGHT, MIN_FACE_SIZE


class FaceDetector:
    """
    Envuelve cv2.FaceDetectorYN (modelo YuNet ONNX).
    Cada fila del resultado: [x, y, w, h, ojo_d_x, ojo_d_y, ojo_i_x, ojo_i_y,
                               nariz_x, nariz_y, boca_d_x, boca_d_y,
                               boca_i_x, boca_i_y, score]  → shape (N, 15)
    """

    def __init__(self) -> None:
        if not Path(YUNET_MODEL).exists():
            raise FileNotFoundError(
                f"Modelo YuNet no encontrado: {YUNET_MODEL}\n"
                "Ejecuta setup_models.py primero."
            )
        self._detector = cv2.FaceDetectorYN.create(
            model          = YUNET_MODEL,
            config         = "",
            input_size     = (FRAME_WIDTH, FRAME_HEIGHT),
            score_threshold = 0.6,
            nms_threshold  = 0.3,
            top_k          = 100,
        )
        self._w = FRAME_WIDTH
        self._h = FRAME_HEIGHT

    def _sync_size(self, w: int, h: int) -> None:
        if w != self._w or h != self._h:
            self._detector.setInputSize((w, h))
            self._w, self._h = w, h

    def detect(self, frame: np.ndarray) -> np.ndarray | None:
        """
        Detecta rostros en el frame.
        Retorna array (N, 15) con rostros válidos, o None si no hay.
        """
        h, w = frame.shape[:2]
        self._sync_size(w, h)
        _, faces = self._detector.detect(frame)
        if faces is None or len(faces) == 0:
            return None
        # Filtrar por tamaño mínimo
        valid = [f for f in faces if f[2] >= MIN_FACE_SIZE and f[3] >= MIN_FACE_SIZE]
        return np.array(valid, dtype=np.float32) if valid else None

    def count(self, frame: np.ndarray) -> int:
        faces = self.detect(frame)
        return 0 if faces is None else len(faces)
