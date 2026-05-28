"""
face_embedder.py — Extracción de embeddings con SFace (cv2.FaceRecognizerSF).
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path

from config import SFACE_MODEL


class FaceEmbedder:
    """
    Envuelve cv2.FaceRecognizerSF (modelo SFace ONNX, 128 dimensiones).
    No requiere TensorFlow en runtime; usa OpenCV DNN directamente.
    """

    def __init__(self) -> None:
        if not Path(SFACE_MODEL).exists():
            raise FileNotFoundError(
                f"Modelo SFace no encontrado: {SFACE_MODEL}\n"
                "Ejecuta setup_models.py primero."
            )
        self._recognizer = cv2.FaceRecognizerSF.create(SFACE_MODEL, "")

    def extract(self, frame: np.ndarray, face_info: np.ndarray) -> np.ndarray:
        """
        Alinea el rostro y extrae su embedding.
        face_info: fila única del resultado de FaceDetector (shape (15,)).
        Retorna vector float32 de 128 dimensiones normalizado.
        """
        aligned = self._recognizer.alignCrop(frame, face_info)
        feature = self._recognizer.feature(aligned)
        return feature.flatten().astype(np.float32)

    def similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """
        Similitud coseno entre dos embeddings.
        Rango [0, 1]: mayor = más similar.
        dis_type=0 → cosine similarity  (FR_COSINE no existe en OpenCV 4.13)
        """
        return float(
            self._recognizer.match(
                feat1.reshape(1, -1),
                feat2.reshape(1, -1),
                0,  # 0 = cosine similarity, 1 = L2 distance
            )
        )
