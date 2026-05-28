"""
face_comparator.py — Comparación de embeddings contra el caché en RAM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from config import COSINE_THRESHOLD
from app.recognition.face_embedder import FaceEmbedder


@dataclass
class MatchResult:
    is_known:   bool
    user_id:    Optional[int]
    name:       Optional[str]
    department: Optional[str]
    confidence: float           # 0.0 – 100.0


class FaceComparator:
    """
    Mantiene un caché en memoria de todos los embeddings registrados
    y compara un embedding de consulta contra ellos.
    """

    def __init__(self, embedder: FaceEmbedder) -> None:
        self._embedder = embedder
        # Lista de {user_id, name, department, embedding: np.ndarray}
        self._cache: list[dict] = []

    # ── Gestión del caché ─────────────────────────────────────────────────────

    def load_cache(self, entries: list[dict]) -> None:
        """Reemplaza el caché completo con los registros de la BD."""
        self._cache = entries

    def reload_from_db(self) -> None:
        """Recarga el caché desde la base de datos."""
        from app.database.db_manager import load_all_embeddings
        self._cache = load_all_embeddings()

    def append(
        self, user_id: int, name: str, department: str, embedding: np.ndarray
    ) -> None:
        self._cache.append({
            "user_id":    user_id,
            "name":       name,
            "department": department,
            "embedding":  embedding,
        })

    def remove_user(self, user_id: int) -> None:
        self._cache = [e for e in self._cache if e["user_id"] != user_id]

    def cache_size(self) -> int:
        return len(self._cache)

    # ── Reconocimiento ────────────────────────────────────────────────────────

    def match(self, query: np.ndarray) -> MatchResult:
        """
        Busca el mejor match para el embedding dado.
        Retorna MatchResult con is_known=True si supera el umbral.
        """
        if not self._cache:
            return MatchResult(False, None, None, None, 0.0)

        best_score = -1.0
        best_entry: Optional[dict] = None

        for entry in self._cache:
            score = self._embedder.similarity(query, entry["embedding"])
            if score > best_score:
                best_score = score
                best_entry = entry

        confidence = round(best_score * 100.0, 1)

        if best_score >= COSINE_THRESHOLD and best_entry is not None:
            return MatchResult(
                True,
                best_entry["user_id"],
                best_entry["name"],
                best_entry["department"],
                confidence,
            )
        return MatchResult(False, None, None, None, confidence)

    # ── Detección de duplicados ───────────────────────────────────────────────

    def find_duplicate(
        self, query: np.ndarray, threshold: Optional[float] = None
    ) -> Optional[dict]:
        """
        Verifica si el rostro ya existe en el caché.
        Retorna {user_id, name, department} si es duplicado, o None.
        """
        thr = threshold if threshold is not None else COSINE_THRESHOLD
        if not self._cache:
            return None

        best_score = -1.0
        best_entry: Optional[dict] = None

        for entry in self._cache:
            score = self._embedder.similarity(query, entry["embedding"])
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= thr and best_entry is not None:
            return {
                "user_id":    best_entry["user_id"],
                "name":       best_entry["name"],
                "department": best_entry["department"],
            }
        return None
