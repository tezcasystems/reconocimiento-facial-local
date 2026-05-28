"""
image_utils.py — Utilidades de procesamiento de imagen y renderizado de texto.
Usa Pillow para texto Unicode (soporte de tildes y caracteres especiales).
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Fuente tipográfica ─────────────────────────────────────────────────────────
_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}
_FONT_PATH: str | None = None

_WINDOWS_FONTS = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
]


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    global _FONT_PATH
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]

    if _FONT_PATH is None:
        for fp in _WINDOWS_FONTS:
            if Path(fp).exists():
                _FONT_PATH = fp
                break

    try:
        if _FONT_PATH:
            font = ImageFont.truetype(_FONT_PATH, size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    _FONT_CACHE[size] = font
    return font


# ── Renderizado de texto con Pillow ───────────────────────────────────────────

def put_text(
    img: np.ndarray,
    text: str,
    pos: tuple[int, int],
    font_size: int = 18,
    color: tuple[int, int, int] = (255, 255, 255),
    bg_color: tuple[int, int, int] | None = None,
    padding: int = 4,
) -> tuple[int, int]:
    """
    Dibuja texto Unicode sobre img en BGR usando Pillow.
    Retorna (ancho_texto, alto_texto) del área dibujada.
    """
    font = _get_font(font_size)
    pil  = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x, y = pos

    if bg_color is not None:
        r, g, b = bg_color
        draw.rectangle(
            (x - padding, y - padding, x + tw + padding, y + th + padding),
            fill=(r, g, b),
        )

    r, g, b = color
    draw.text((x, y), text, font=font, fill=(r, g, b))

    img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return tw, th


def put_text_centered(
    img: np.ndarray,
    text: str,
    cy: int,
    font_size: int = 18,
    color: tuple[int, int, int] = (255, 255, 255),
    bg_color: tuple[int, int, int] | None = None,
) -> None:
    """Dibuja texto centrado horizontalmente en la imagen."""
    font = _get_font(font_size)
    pil  = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    h, w = img.shape[:2]
    x    = (w - tw) // 2
    y    = cy - th // 2

    if bg_color is not None:
        r, g, b = bg_color
        draw.rectangle((x - 6, y - 4, x + tw + 6, y + th + 4), fill=(r, g, b))

    r, g, b = color
    draw.text((x, y), text, font=font, fill=(r, g, b))
    img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


# ── Overlays y formas ─────────────────────────────────────────────────────────

def semi_transparent_rect(
    img: np.ndarray,
    pt1: tuple[int, int],
    pt2: tuple[int, int],
    color: tuple[int, int, int],
    alpha: float = 0.55,
) -> None:
    """Rectángulo semitransparente sobre la imagen."""
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, cv2.FILLED)
    cv2.addWeighted(overlay, alpha, img, 1.0 - alpha, 0, img)


def draw_progress_bar(
    img: np.ndarray,
    x: int, y: int,
    width: int, height: int,
    progress: float,           # 0.0 – 1.0
    color_bg: tuple  = (60, 60, 60),
    color_fill: tuple = (0, 200, 0),
) -> None:
    """Dibuja una barra de progreso horizontal."""
    cv2.rectangle(img, (x, y), (x + width, y + height), color_bg, cv2.FILLED)
    filled = int(width * min(1.0, max(0.0, progress)))
    if filled > 0:
        cv2.rectangle(img, (x, y), (x + filled, y + height), color_fill, cv2.FILLED)
    cv2.rectangle(img, (x, y), (x + width, y + height), (100, 100, 100), 1)


# ── Validación de calidad de imagen ──────────────────────────────────────────

def compute_brightness(frame: np.ndarray) -> float:
    """Brillo promedio de un frame (0–255)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def compute_blur(face_crop: np.ndarray) -> float:
    """Varianza Laplaciana: mayor = más nítido."""
    if face_crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def crop_face(frame: np.ndarray, box: tuple) -> np.ndarray:
    """Recorta el rostro del frame dado (x, y, w, h)."""
    x, y, w, h = (int(v) for v in box)
    x = max(0, x)
    y = max(0, y)
    return frame[y: y + h, x: x + w].copy()
