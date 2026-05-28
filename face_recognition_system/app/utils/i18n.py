"""
i18n.py — Sistema de internacionalización ES/EN.
"""
from __future__ import annotations
from config import DEFAULT_LANGUAGE

_LANG: str = DEFAULT_LANGUAGE

STRINGS: dict[str, dict[str, str]] = {
    # ── Reconocimiento ────────────────────────────────────────────────────────
    "known":               {"es": "Conocido",                       "en": "Known"},
    "unknown":             {"es": "Desconocido",                    "en": "Unknown"},
    "multiple_faces":      {"es": "Multiples rostros detectados",   "en": "Multiple faces detected"},
    "multiple_faces_msg":  {"es": "Solo una persona frente a la camara, por favor.",
                            "en": "Please ensure only one person faces the camera."},
    "no_face":             {"es": "Sin rostro",                     "en": "No face"},
    "confidence":          {"es": "Confianza",                      "en": "Confidence"},
    "department":          {"es": "Depto.",                         "en": "Dept."},
    "access_granted":      {"es": "ACCESO CONCEDIDO",               "en": "ACCESS GRANTED"},
    "access_denied":       {"es": "ACCESO DENEGADO",                "en": "ACCESS DENIED"},
    "hint_admin":          {"es": "Ctrl+A: Admin  |  Q: Salir",     "en": "Ctrl+A: Admin  |  Q: Quit"},

    # ── Autenticación admin ───────────────────────────────────────────────────
    "admin_auth_title":    {"es": "ACCESO ADMINISTRADOR",           "en": "ADMIN LOGIN"},
    "enter_password":      {"es": "Contrasena:",                    "en": "Password:"},
    "wrong_password":      {"es": "Contrasena incorrecta",          "en": "Wrong password"},
    "esc_cancel":          {"es": "ESC: Cancelar",                  "en": "ESC: Cancel"},

    # ── Menú admin ────────────────────────────────────────────────────────────
    "admin_menu_title":    {"es": "MODO ADMINISTRADOR",             "en": "ADMIN MODE"},
    "admin_menu_r":        {"es": "[R] Registrar usuario",          "en": "[R] Register user"},
    "admin_menu_v":        {"es": "[V] Ver / Editar usuarios",      "en": "[V] View / Edit users"},
    "admin_menu_l":        {"es": "[L] Log de accesos",             "en": "[L] Access log"},
    "admin_menu_c":        {"es": "[C] Cambiar camara",             "en": "[C] Change camera"},
    "admin_menu_i":        {"es": "[I] Cambiar idioma",             "en": "[I] Change language"},
    "admin_menu_esc":      {"es": "[ESC] Volver",                   "en": "[ESC] Back"},

    # ── Registro ──────────────────────────────────────────────────────────────
    "reg_title":           {"es": "REGISTRO DE USUARIO",            "en": "USER REGISTRATION"},
    "reg_no_face":         {"es": "No se detecta rostro",           "en": "No face detected"},
    "reg_poor_light":      {"es": "Iluminacion insuficiente",       "en": "Poor lighting"},
    "reg_too_small":       {"es": "Acerquese mas a la camara",      "en": "Move closer to the camera"},
    "reg_blurry":          {"es": "Imagen borrosa, quieto",         "en": "Blurry image, stay still"},
    "reg_multiple":        {"es": "Solo una persona en pantalla",   "en": "Only one person in frame"},
    "reg_center":          {"es": "Mire al frente",                 "en": "Look straight ahead"},
    "reg_left":            {"es": "Gire a la izquierda",            "en": "Turn left"},
    "reg_right":           {"es": "Gire a la derecha",              "en": "Turn right"},
    "reg_up":              {"es": "Mire hacia arriba",              "en": "Look up"},
    "reg_down":            {"es": "Mire hacia abajo",               "en": "Look down"},
    "reg_smile":           {"es": "Ahora sonria",                   "en": "Now smile"},
    "reg_progress":        {"es": "Capturas:",                      "en": "Captures:"},
    "reg_movement":        {"es": "Movimiento",                     "en": "Movement"},
    "reg_of":              {"es": "de",                             "en": "of"},
    "reg_done_capture":    {"es": "Captura completa!",              "en": "Capture complete!"},
    "reg_enter_name":      {"es": "Nombre completo:",               "en": "Full name:"},
    "reg_enter_dept":      {"es": "Departamento:",                  "en": "Department:"},
    "reg_saved":           {"es": "Usuario guardado correctamente.", "en": "User saved successfully."},
    "reg_duplicate":       {"es": "Rostro ya registrado como:",     "en": "Face already registered as:"},
    "reg_not_enough":      {"es": "Capturas insuficientes, intente de nuevo.", "en": "Not enough captures, try again."},
    "reg_esc_cancel":      {"es": "[ESC] Cancelar",                 "en": "[ESC] Cancel"},
    "reg_enter_confirm":   {"es": "[ENTER] Confirmar",              "en": "[ENTER] Confirm"},
    "reg_hint_dept_skip":  {"es": "[ENTER] sin texto = sin depto.", "en": "[ENTER] empty = no dept."},

    # ── Lista de usuarios ──────────────────────────────────────────────────────
    "users_title":         {"es": "USUARIOS REGISTRADOS",           "en": "REGISTERED USERS"},
    "users_no_users":      {"es": "No hay usuarios registrados.",   "en": "No registered users."},
    "users_id":            {"es": "ID",                             "en": "ID"},
    "users_name":          {"es": "Nombre",                         "en": "Name"},
    "users_dept":          {"es": "Departamento",                   "en": "Department"},
    "users_date":          {"es": "Fecha",                          "en": "Date"},
    "users_nav":           {"es": "[Arriba/Abajo] Navegar",         "en": "[Up/Down] Navigate"},
    "users_edit_key":      {"es": "[E] Editar  [D] Eliminar  [ESC] Volver",
                            "en": "[E] Edit  [D] Delete  [ESC] Back"},
    "users_confirm_del":   {"es": "Eliminar usuario? [S] Si  [N] No",
                            "en": "Delete user? [Y] Yes  [N] No"},
    "users_deleted":       {"es": "Usuario eliminado.",             "en": "User deleted."},
    "users_edit_title":    {"es": "EDITAR USUARIO",                 "en": "EDIT USER"},
    "users_saved":         {"es": "Cambios guardados.",             "en": "Changes saved."},

    # ── Log de accesos ─────────────────────────────────────────────────────────
    "log_title":           {"es": "LOG DE ACCESOS",                 "en": "ACCESS LOG"},
    "log_no_entries":      {"es": "Sin registros de acceso.",       "en": "No access records."},
    "log_time":            {"es": "Hora",                           "en": "Time"},
    "log_user":            {"es": "Usuario",                        "en": "User"},
    "log_dept":            {"es": "Depto.",                         "en": "Dept."},
    "log_status":          {"es": "Estado",                         "en": "Status"},
    "log_conf":            {"es": "Conf.",                          "en": "Conf."},
    "log_granted":         {"es": "Concedido",                      "en": "Granted"},
    "log_denied":          {"es": "Denegado",                       "en": "Denied"},
    "log_unknown":         {"es": "Desconocido",                    "en": "Unknown"},
    "log_scroll":          {"es": "[Arriba/Abajo] Desplazar  [ESC] Volver",
                            "en": "[Up/Down] Scroll  [ESC] Back"},

    # ── Selección de cámara ────────────────────────────────────────────────────
    "cam_title":           {"es": "SELECCION DE CAMARA",            "en": "CAMERA SELECTION"},
    "cam_found":           {"es": "Camaras disponibles:",           "en": "Available cameras:"},
    "cam_none":            {"es": "No se detectaron camaras.",      "en": "No cameras detected."},
    "cam_current":         {"es": "Activa:",                        "en": "Active:"},
    "cam_select_hint":     {"es": "[0-9] Seleccionar  [ESC] Cancelar",
                            "en": "[0-9] Select  [ESC] Cancel"},
    "cam_switched":        {"es": "Camara cambiada.",               "en": "Camera switched."},
    "cam_error":           {"es": "No se pudo abrir esa camara.",   "en": "Could not open that camera."},

    # ── Sistema ────────────────────────────────────────────────────────────────
    "language_es":         {"es": "Idioma: Espanol",                "en": "Language: Spanish"},
    "language_en":         {"es": "Idioma: Ingles",                 "en": "Language: English"},
}


def t(key: str) -> str:
    """Retorna la cadena traducida al idioma activo."""
    entry = STRINGS.get(key, {})
    return entry.get(_LANG, entry.get("es", key))


def set_language(lang: str) -> None:
    global _LANG
    if lang in ("es", "en"):
        _LANG = lang


def toggle_language() -> str:
    global _LANG
    _LANG = "en" if _LANG == "es" else "es"
    return _LANG


def current_language() -> str:
    return _LANG
