"""
config.py — Configuración global del sistema de reconocimiento facial.
"""
import hashlib
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
DB_PATH    = DATA_DIR / "database" / "face_system.db"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR   = DATA_DIR / "logs"

# ── Cámara ────────────────────────────────────────────────────────────────────
DEFAULT_CAMERA_INDEX   = 0
FRAME_WIDTH            = 640
FRAME_HEIGHT           = 480
PROCESS_EVERY_N_FRAMES = 5      # Procesar 1 de cada 5 frames

# ── Modelos ONNX ──────────────────────────────────────────────────────────────
YUNET_MODEL = str(MODELS_DIR / "face_detection_yunet_2023mar.onnx")
SFACE_MODEL = str(MODELS_DIR / "face_recognition_sface_2021dec.onnx")

YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
SFACE_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)

# ── Umbrales de reconocimiento ────────────────────────────────────────────────
# Similitud coseno: mayor = más similar (rango 0–1).
# EER por defecto: 0.363. Estricto (menos falsos positivos): 0.40
COSINE_THRESHOLD  = 0.40
MIN_FACE_SIZE     = 60      # Ancho/alto mínimo del rostro en píxeles
MIN_BRIGHTNESS    = 40      # Brillo promedio mínimo (0–255)
MAX_BLUR_VARIANCE = 100.0   # Varianza Laplaciana; menor = imagen borrosa

# ── Registro ──────────────────────────────────────────────────────────────────
MIN_EMBEDDINGS_REQUIRED = 50
REGISTRATION_MAX_FRAMES = 900   # ~60 s a ~15 fps de previsualización

MOVEMENT_INSTRUCTIONS = [
    "center",
    "left",
    "right",
    "up",
    "down",
    "smile",
]
FRAMES_PER_MOVEMENT = 150   # Frames asignados por instrucción de movimiento

# ── Administrador ─────────────────────────────────────────────────────────────
_ADMIN_PASSWORD_PLAIN = "admin123"
ADMIN_PASSWORD_HASH   = hashlib.sha256(_ADMIN_PASSWORD_PLAIN.encode()).hexdigest()

# ── Idioma ────────────────────────────────────────────────────────────────────
DEFAULT_LANGUAGE = "es"     # "es" | "en"

# ── Colores de la UI (formato BGR de OpenCV) ──────────────────────────────────
# Paleta "Soft Dark" — tonos desaturados y cálidos, cómodos para la vista.
# Todos los valores están reducidos al ~70-80% de saturación.
COLOR_GREEN   = (95, 190, 110)    # Verde salvia       — acceso concedido
COLOR_RED     = (85, 95, 210)     # Coral suave        — acceso denegado
COLOR_ORANGE  = (65, 155, 215)    # Ámbar cálido       — advertencias / progreso
COLOR_BLUE    = (195, 130, 70)    # Azul pizarra       — selección / bordes
COLOR_WHITE   = (220, 228, 232)   # Blanco cálido      — texto principal
COLOR_BLACK   = (0, 0, 0)
COLOR_YELLOW  = (85, 185, 220)    # Dorado cálido      — títulos / destacados
COLOR_GRAY    = (148, 148, 148)   # Gris neutro        — texto secundario
COLOR_DARK    = (28, 28, 28)      # Casi negro         — fondos de paneles
COLOR_LIGHT   = (190, 193, 195)   # Gris claro cálido  — ítems de lista

# ── Ventana ───────────────────────────────────────────────────────────────────
WINDOW_NAME = "Face Recognition System"
