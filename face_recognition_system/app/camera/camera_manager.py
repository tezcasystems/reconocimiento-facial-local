"""
camera_manager.py — Gestión de la webcam con selección de índice.
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Optional

from config import DEFAULT_CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


class CameraManager:
    """Encapsula la captura de video con soporte para múltiples cámaras."""

    def __init__(self, index: int = DEFAULT_CAMERA_INDEX) -> None:
        self._index = index
        self._cap: Optional[cv2.VideoCapture] = None
        self._open()

    def _open(self) -> None:
        if self._cap and self._cap.isOpened():
            self._cap.release()
        self._cap = cv2.VideoCapture(self._index, cv2.CAP_DSHOW)
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # Reducir latencia

    def is_open(self) -> bool:
        return bool(self._cap and self._cap.isOpened())

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        if not self.is_open():
            return False, None
        ret, frame = self._cap.read()
        return ret, frame

    def switch_camera(self, index: int) -> bool:
        """Cambia a otro índice de cámara. Retorna True si tuvo éxito."""
        old_index = self._index
        self._index = index
        self._open()
        if self.is_open():
            ret, _ = self._cap.read()
            if ret:
                return True
        # Revertir si falla
        self._index = old_index
        self._open()
        return False

    def current_index(self) -> int:
        return self._index

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None

    def __del__(self) -> None:
        self.release()

    @staticmethod
    def detect_available_cameras(max_check: int = 6) -> list[int]:
        """Retorna los índices de cámaras accesibles."""
        available: list[int] = []
        for i in range(max_check):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
            cap.release()
        return available
