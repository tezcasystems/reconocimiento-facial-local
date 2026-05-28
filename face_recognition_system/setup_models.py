"""
setup_models.py — Descarga los modelos ONNX de YuNet y SFace desde el zoo oficial de OpenCV.
Ejecutar una sola vez antes de iniciar el sistema.
"""
import sys
from pathlib import Path

# Resolver imports desde la raíz del proyecto
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import requests
from config import MODELS_DIR, YUNET_MODEL, SFACE_MODEL, YUNET_URL, SFACE_URL


def _download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"  [OK] Ya existe: {dest.name}")
        return
    print(f"  Descargando {dest.name} ...")
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r    {pct:.1f}%", end="", flush=True)
        print(f"\r  [OK] {dest.name} ({downloaded // 1024} KB)")
    except Exception as exc:
        print(f"\n  [ERROR] No se pudo descargar {dest.name}: {exc}")
        if dest.exists():
            dest.unlink()
        sys.exit(1)


def main() -> None:
    print("=" * 50)
    print("  Configuración de modelos ONNX")
    print("=" * 50)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    _download(YUNET_URL, Path(YUNET_MODEL))
    _download(SFACE_URL, Path(SFACE_MODEL))

    print()
    print("Modelos listos. Ahora puedes ejecutar:  python main.py")


if __name__ == "__main__":
    main()
