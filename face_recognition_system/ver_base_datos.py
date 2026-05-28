"""
ver_base_datos.py
=================
Visor interactivo de la base de datos del sistema de reconocimiento facial.

Uso:
    cd face_recognition_system
    python ver_base_datos.py

Opciones en el menú:
    1 - Ver todos los usuarios registrados
    2 - Ver embeddings por usuario
    3 - Ver log de accesos recientes
    4 - Buscar usuario por nombre
    5 - Estadísticas generales
    0 - Salir
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import sqlite3
from datetime import datetime
from config import DB_PATH


# ── Helpers de formato ────────────────────────────────────────────────────────

def _linea(char="─", n=72):
    print(char * n)

def _titulo(texto):
    _linea("═")
    print(f"  {texto}")
    _linea("═")

def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Opción 1: Usuarios ────────────────────────────────────────────────────────

def ver_usuarios():
    _titulo("USUARIOS REGISTRADOS")
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT id, name, department, created_at, active FROM users ORDER BY id"
        ).fetchall()

    if not rows:
        print("  (sin usuarios)")
        return

    print(f"  {'ID':<5} {'Nombre':<25} {'Departamento':<20} {'Fecha registro':<22} {'Activo'}")
    _linea()
    for r in rows:
        activo = "Sí" if r["active"] else "No"
        print(f"  {r['id']:<5} {r['name']:<25} {(r['department'] or ''):<20} {r['created_at']:<22} {activo}")

    print(f"\n  Total: {len(rows)} usuario(s)")


# ── Opción 2: Embeddings por usuario ─────────────────────────────────────────

def ver_embeddings():
    _titulo("EMBEDDINGS POR USUARIO")
    with _conectar() as conn:
        rows = conn.execute("""
            SELECT u.id, u.name, COUNT(e.id) as total,
                   MIN(e.created_at) as primera,
                   MAX(e.created_at) as ultima
            FROM   users u
            LEFT JOIN embeddings e ON e.user_id = u.id
            WHERE  u.active = 1
            GROUP  BY u.id
            ORDER  BY u.id
        """).fetchall()

    if not rows:
        print("  (sin datos)")
        return

    print(f"  {'ID':<5} {'Nombre':<25} {'Embeddings':<12} {'Primer registro':<22} {'Último registro'}")
    _linea()
    for r in rows:
        print(f"  {r['id']:<5} {r['name']:<25} {r['total']:<12} {(r['primera'] or 'N/A'):<22} {r['ultima'] or 'N/A'}")

    total_emb = sum(r["total"] for r in rows)
    print(f"\n  Total embeddings: {total_emb}")
    print("  Nota: se requieren mínimo 50 embeddings por usuario para reconocimiento óptimo.")


# ── Opción 3: Log de accesos ──────────────────────────────────────────────────

def ver_logs(limite=50):
    _titulo(f"LOG DE ACCESOS (últimos {limite})")
    with _conectar() as conn:
        rows = conn.execute("""
            SELECT timestamp, user_name, department, confidence, status
            FROM   access_logs
            ORDER  BY id DESC
            LIMIT  ?
        """, (limite,)).fetchall()

    if not rows:
        print("  (sin registros de acceso)")
        return

    print(f"  {'Fecha/Hora':<22} {'Usuario':<20} {'Departamento':<16} {'Confianza':<11} {'Estado'}")
    _linea()
    for r in rows:
        nombre = r["user_name"] or "Desconocido"
        depto  = r["department"] or "—"
        conf   = f"{r['confidence']:.1f}%"
        estado = "CONCEDIDO" if r["status"] == "granted" else "DENEGADO"
        print(f"  {r['timestamp']:<22} {nombre:<20} {depto:<16} {conf:<11} {estado}")

    # Resumen
    with _conectar() as conn:
        stats = conn.execute(
            "SELECT COUNT(*) total, SUM(status='granted') concedidos, SUM(status='unknown') denegados FROM access_logs"
        ).fetchone()
    print(f"\n  Total histórico: {stats['total']}  |  Concedidos: {stats['concedidos']}  |  Denegados: {stats['denegados']}")


# ── Opción 4: Buscar usuario ──────────────────────────────────────────────────

def buscar_usuario():
    _titulo("BUSCAR USUARIO POR NOMBRE")
    termino = input("  Introduce nombre (o parte): ").strip()
    if not termino:
        return

    with _conectar() as conn:
        rows = conn.execute(
            "SELECT id, name, department, created_at FROM users WHERE name LIKE ? AND active=1",
            (f"%{termino}%",)
        ).fetchall()

    if not rows:
        print("  No se encontraron usuarios.")
        return

    for r in rows:
        _linea("─", 50)
        print(f"  ID          : {r['id']}")
        print(f"  Nombre      : {r['name']}")
        print(f"  Departamento: {r['department'] or '—'}")
        print(f"  Registrado  : {r['created_at']}")

        with _conectar() as conn2:
            cnt = conn2.execute(
                "SELECT COUNT(*) n FROM embeddings WHERE user_id=?", (r["id"],)
            ).fetchone()["n"]
            logs = conn2.execute(
                "SELECT COUNT(*) n, MAX(timestamp) ultimo FROM access_logs WHERE user_id=?", (r["id"],)
            ).fetchone()

        print(f"  Embeddings  : {cnt}")
        print(f"  Accesos log : {logs['n']}  |  Último: {logs['ultimo'] or 'nunca'}")


# ── Opción 5: Estadísticas ────────────────────────────────────────────────────

def ver_estadisticas():
    _titulo("ESTADÍSTICAS GENERALES")
    with _conectar() as conn:
        usuarios     = conn.execute("SELECT COUNT(*) n FROM users WHERE active=1").fetchone()["n"]
        embeddings   = conn.execute("SELECT COUNT(*) n FROM embeddings").fetchone()["n"]
        logs_total   = conn.execute("SELECT COUNT(*) n FROM access_logs").fetchone()["n"]
        logs_granted = conn.execute("SELECT COUNT(*) n FROM access_logs WHERE status='granted'").fetchone()["n"]
        logs_unknown = conn.execute("SELECT COUNT(*) n FROM access_logs WHERE status='unknown'").fetchone()["n"]
        ultimo_log   = conn.execute("SELECT MAX(timestamp) t FROM access_logs").fetchone()["t"]
        db_size_kb   = Path(DB_PATH).stat().st_size // 1024 if Path(DB_PATH).exists() else 0

    emb_por_usuario = (embeddings / usuarios) if usuarios > 0 else 0
    tasa_exito = (logs_granted / logs_total * 100) if logs_total > 0 else 0

    print(f"  Usuarios activos        : {usuarios}")
    print(f"  Embeddings totales      : {embeddings}  (promedio {emb_por_usuario:.1f} por usuario)")
    print(f"  Registros de acceso     : {logs_total}")
    print(f"    - Accesos concedidos  : {logs_granted}  ({tasa_exito:.1f}%)")
    print(f"    - Accesos denegados   : {logs_unknown}")
    print(f"  Último acceso           : {ultimo_log or 'nunca'}")
    print(f"  Tamaño base de datos    : {db_size_kb} KB  ({DB_PATH})")


# ── Menú principal ────────────────────────────────────────────────────────────

def menu():
    while True:
        print()
        _linea("═")
        print("  VISOR DE BASE DE DATOS — Sistema de Reconocimiento Facial")
        _linea("═")
        print("  1  Ver usuarios registrados")
        print("  2  Ver embeddings por usuario")
        print("  3  Ver log de accesos")
        print("  4  Buscar usuario por nombre")
        print("  5  Estadísticas generales")
        print("  0  Salir")
        _linea()
        opcion = input("  Selecciona opción: ").strip()

        if opcion == "1":
            ver_usuarios()
        elif opcion == "2":
            ver_embeddings()
        elif opcion == "3":
            n = input("  ¿Cuántos registros mostrar? [50]: ").strip()
            ver_logs(int(n) if n.isdigit() else 50)
        elif opcion == "4":
            buscar_usuario()
        elif opcion == "5":
            ver_estadisticas()
        elif opcion == "0":
            print("  Saliendo...")
            break
        else:
            print("  Opción no válida.")

        input("\n  Presiona ENTER para continuar...")


if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        print(f"[ERROR] Base de datos no encontrada: {DB_PATH}")
        print("  Ejecuta primero: python main.py")
        sys.exit(1)
    menu()
