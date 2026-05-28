"""
main.py — Punto de entrada del sistema de reconocimiento facial.

Uso:
    cd face_recognition_system
    python main.py

Primera vez:
    python setup_models.py   (descarga los modelos ONNX ~40 MB)
"""
import sys
from pathlib import Path

# Asegurar que los imports resuelvan desde este directorio
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ui.main_app import MainApp


def main() -> None:
    print("[INFO] Iniciando sistema de reconocimiento facial...")

    # Verificar modelos antes de iniciar
    from config import YUNET_MODEL, SFACE_MODEL
    missing = [m for m in (YUNET_MODEL, SFACE_MODEL) if not Path(m).exists()]
    if missing:
        print("ERROR: Faltan modelos ONNX. Ejecuta primero:")
        print("       python setup_models.py")
        for m in missing:
            print(f"       Falta: {m}")
        sys.exit(1)

    print("[INFO] Modelos ONNX encontrados. Cargando aplicación...")

    try:
        app = MainApp()
        app.run()
    except Exception as e:
        print(f"[ERROR] Fallo al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
