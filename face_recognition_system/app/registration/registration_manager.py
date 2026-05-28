"""
registration_manager.py — Máquina de estados para el flujo de registro de usuarios.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import numpy as np

from config import (
    MIN_EMBEDDINGS_REQUIRED,
    REGISTRATION_MAX_FRAMES,
    MOVEMENT_INSTRUCTIONS,
    FRAMES_PER_MOVEMENT,
    MIN_BRIGHTNESS,
    MAX_BLUR_VARIANCE,
    MIN_FACE_SIZE,
)
from app.utils.image_utils import compute_brightness, compute_blur, crop_face
from app.recognition.face_detector import FaceDetector
from app.recognition.face_embedder import FaceEmbedder
from app.recognition.face_comparator import FaceComparator


class RegState(Enum):
    DETECTING        = auto()   # Esperando que aparezca un rostro
    CAPTURING        = auto()   # Capturando embeddings con instrucciones
    DUPLICATE_FOUND  = auto()   # Rostro ya existe en el sistema
    ENTERING_NAME    = auto()   # Esperando nombre por teclado
    ENTERING_DEPT    = auto()   # Esperando departamento por teclado
    SAVING           = auto()   # Guardando en BD
    DONE             = auto()   # Registro completado
    CANCELLED        = auto()   # Usuario canceló


@dataclass
class RegSession:
    state:            RegState        = RegState.DETECTING
    embeddings:       list            = field(default_factory=list)
    frame_count:      int             = 0
    movement_index:   int             = 0
    movement_frames:  int             = 0
    name_input:       str             = ""
    dept_input:       str             = ""
    name:             str             = ""
    department:       str             = ""
    duplicate_name:   Optional[str]   = None
    duplicate_dept:   Optional[str]   = None
    validation_msg:   str             = ""
    last_face_info:   Optional[np.ndarray] = None


class RegistrationManager:
    """Gestiona el flujo completo de registro de un nuevo usuario."""

    def __init__(
        self,
        detector:   FaceDetector,
        embedder:   FaceEmbedder,
        comparator: FaceComparator,
    ) -> None:
        self._detector   = detector
        self._embedder   = embedder
        self._comparator = comparator
        self.session     = RegSession()

    def reset(self) -> None:
        self.session = RegSession()

    # ── Instrucción de movimiento activa ──────────────────────────────────────

    def current_movement_key(self) -> str:
        idx = self.session.movement_index
        if idx < len(MOVEMENT_INSTRUCTIONS):
            return MOVEMENT_INSTRUCTIONS[idx]
        return "done"

    def progress_ratio(self) -> float:
        return min(1.0, len(self.session.embeddings) / MIN_EMBEDDINGS_REQUIRED)

    # ── Procesamiento de frame ────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> RegSession:
        sess = self.session

        # No procesar en estados de entrada de datos
        if sess.state in (
            RegState.ENTERING_NAME,
            RegState.ENTERING_DEPT,
            RegState.DONE,
            RegState.CANCELLED,
            RegState.DUPLICATE_FOUND,
            RegState.SAVING,
        ):
            return sess

        # ── Calidad de iluminación ────────────────────────────────────────────
        brightness = compute_brightness(frame)
        if brightness < MIN_BRIGHTNESS:
            sess.validation_msg = "reg_poor_light"
            sess.state = RegState.DETECTING
            return sess

        # ── Detección de rostros ──────────────────────────────────────────────
        faces = self._detector.detect(frame)

        if faces is None:
            sess.validation_msg = "reg_no_face"
            sess.state = RegState.DETECTING
            return sess

        if len(faces) > 1:
            sess.validation_msg = "reg_multiple"
            sess.state = RegState.DETECTING
            return sess

        face_info = faces[0]
        x, y, w, h = int(face_info[0]), int(face_info[1]), int(face_info[2]), int(face_info[3])

        if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
            sess.validation_msg = "reg_too_small"
            sess.state = RegState.DETECTING
            return sess

        face_crop = crop_face(frame, (x, y, w, h))
        blur_val  = compute_blur(face_crop)
        if blur_val < MAX_BLUR_VARIANCE:
            sess.validation_msg = "reg_blurry"
            sess.state = RegState.DETECTING
            return sess

        sess.validation_msg = ""
        sess.last_face_info = face_info

        # ── Activar captura ───────────────────────────────────────────────────
        if sess.state == RegState.DETECTING:
            sess.state = RegState.CAPTURING

        # ── Extraer embedding ─────────────────────────────────────────────────
        try:
            embedding = self._embedder.extract(frame, face_info)
        except Exception:
            return sess

        sess.embeddings.append(embedding)
        sess.frame_count    += 1
        sess.movement_frames += 1

        # ── Verificar duplicado temprano (tras 10 capturas) ───────────────────
        if len(sess.embeddings) == 10:
            dup = self._comparator.find_duplicate(embedding)
            if dup:
                sess.duplicate_name = dup["name"]
                sess.duplicate_dept = dup["department"]
                sess.state = RegState.DUPLICATE_FOUND
                return sess

        # ── Avanzar instrucción de movimiento ─────────────────────────────────
        if sess.movement_frames >= FRAMES_PER_MOVEMENT:
            sess.movement_index  += 1
            sess.movement_frames  = 0

        # ── Verificar fin de captura ──────────────────────────────────────────
        movements_done = sess.movement_index >= len(MOVEMENT_INSTRUCTIONS)
        enough         = len(sess.embeddings) >= MIN_EMBEDDINGS_REQUIRED
        timeout        = sess.frame_count >= REGISTRATION_MAX_FRAMES

        if (movements_done and enough) or (timeout and enough):
            sess.state = RegState.ENTERING_NAME
        elif timeout and not enough:
            # Tiempo agotado sin suficientes capturas → reiniciar
            sess.validation_msg = "reg_not_enough"
            self.reset()

        return sess

    # ── Manejo de teclado: nombre ─────────────────────────────────────────────

    def handle_key_name(self, key: int) -> None:
        sess = self.session
        if sess.state != RegState.ENTERING_NAME:
            return
        if key == 13:                           # ENTER
            if sess.name_input.strip():
                sess.name  = sess.name_input.strip()
                sess.state = RegState.ENTERING_DEPT
        elif key == 27:                         # ESC
            sess.state = RegState.CANCELLED
        elif key in (8, 127):                   # BACKSPACE / DEL
            sess.name_input = sess.name_input[:-1]
        elif 32 <= key <= 126:
            sess.name_input += chr(key)

    # ── Manejo de teclado: departamento ──────────────────────────────────────

    def handle_key_dept(self, key: int) -> None:
        sess = self.session
        if sess.state != RegState.ENTERING_DEPT:
            return
        if key == 13:                           # ENTER
            sess.department = sess.dept_input.strip()
            sess.state      = RegState.SAVING
        elif key == 27:                         # ESC
            sess.state = RegState.CANCELLED
        elif key in (8, 127):
            sess.dept_input = sess.dept_input[:-1]
        elif 32 <= key <= 126:
            sess.dept_input += chr(key)
