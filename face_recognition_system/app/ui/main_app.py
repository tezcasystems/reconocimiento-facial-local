"""
main_app.py — Controlador principal de la aplicación.
Máquina de estados que gestiona todas las vistas de la UI con OpenCV.
"""
from __future__ import annotations

import hashlib
import time
from enum import Enum, auto
from typing import Optional

import cv2
import numpy as np

import config
from app.camera.camera_manager import CameraManager
from app.database import db_manager
from app.recognition.face_comparator import FaceComparator, MatchResult
from app.recognition.face_detector import FaceDetector
from app.recognition.face_embedder import FaceEmbedder
from app.registration.registration_manager import RegState, RegistrationManager
from app.utils import i18n
from app.utils.image_utils import (
    draw_progress_bar,
    put_text,
    put_text_centered,
    semi_transparent_rect,
)


# ── Teclas de flecha (Windows, códigos raw de cv2.waitKey sin máscara) ─────────
_KEY_UP    = 2490368
_KEY_DOWN  = 2621440
_KEY_LEFT  = 2424832
_KEY_RIGHT = 2555904


# ── Estados de la aplicación ──────────────────────────────────────────────────

class AppState(Enum):
    RECOGNITION   = auto()
    ADMIN_AUTH    = auto()
    ADMIN_MENU    = auto()
    REGISTER      = auto()
    USER_LIST     = auto()
    USER_EDIT     = auto()
    LOG_VIEW      = auto()
    CAM_SELECT    = auto()


# ── Clase principal ───────────────────────────────────────────────────────────

class MainApp:

    _FRAME_SKIP = config.PROCESS_EVERY_N_FRAMES

    def __init__(self) -> None:
        db_manager.initialize_db()

        self._camera     = CameraManager(config.DEFAULT_CAMERA_INDEX)
        self._detector   = FaceDetector()
        self._embedder   = FaceEmbedder()
        self._comparator = FaceComparator(self._embedder)
        self._reg_mgr    = RegistrationManager(
            self._detector, self._embedder, self._comparator
        )

        # Cargar embeddings en caché
        self._comparator.load_cache(db_manager.load_all_embeddings())

        self._state: AppState = AppState.RECOGNITION

        # Reconocimiento
        self._frame_counter      = 0
        self._last_result: Optional[MatchResult] = None
        self._last_faces: Optional[np.ndarray]   = None
        self._last_frame_display: Optional[np.ndarray] = None

        # Admin auth
        self._pwd_input      = ""
        self._pwd_error      = False
        self._pwd_error_time = 0.0

        # Lista de usuarios
        self._users:          list[dict] = []
        self._user_sel_idx    = 0
        self._user_scroll     = 0
        self._confirm_delete  = False
        self._user_msg        = ""
        self._user_msg_time   = 0.0

        # Edición de usuario
        self._edit_user:    Optional[dict] = None
        self._edit_field    = 0            # 0 = nombre, 1 = departamento
        self._edit_name_buf = ""
        self._edit_dept_buf = ""

        # Log de accesos
        self._logs:       list[dict] = []
        self._log_scroll  = 0

        # Selección de cámara
        self._available_cams: list[int] = []
        self._cam_msg         = ""
        self._cam_msg_time    = 0.0

        # Cooldown de acceso (evitar múltiples logs por el mismo evento)
        self._last_access_log_time  = 0.0
        self._last_access_user_id: Optional[int] = None

    # ── Bucle principal ───────────────────────────────────────────────────────

    def run(self) -> None:
        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_NAME, config.FRAME_WIDTH, config.FRAME_HEIGHT)

        print(f"[INFO] Ventana creada: {config.WINDOW_NAME}")
        print(f"[INFO] Cámara índice: {config.DEFAULT_CAMERA_INDEX}")
        cam_ok = self._camera.is_open()
        print(f"[INFO] Cámara abierta: {cam_ok}")
        if not cam_ok:
            print("[WARN] No se pudo abrir la cámara. Se mostrará fotograma en negro.")
        print("[INFO] Presiona Q para salir. Ctrl+A para panel de administrador.")

        try:
            loop_count = 0
            while True:
                loop_count += 1
                ret, frame = self._camera.read()
                if not ret or frame is None:
                    frame = self._blank_frame()

                # Leer tecla — waitKeyEx captura flechas y teclas extendidas correctamente
                key_raw = cv2.waitKeyEx(1)
                if key_raw == -1:
                    key = -1
                elif key_raw > 255:
                    key = key_raw           # Arrow keys y otras teclas extendidas
                else:
                    key = key_raw & 0xFF    # Teclas regulares

                # Salir global
                if key in (ord('q'), ord('Q')):
                    print(f"[INFO] Salida por tecla Q (iteración {loop_count}, key_raw={key_raw})")
                    break

                # Despachar al estado activo
                try:
                    display = self._dispatch(frame, key)
                except Exception as e:
                    import traceback
                    print(f"[ERROR dispatch iter={loop_count}] {type(e).__name__}: {e}")
                    traceback.print_exc()
                    break

                cv2.imshow(config.WINDOW_NAME, display)

        finally:
            self._camera.release()
            cv2.destroyAllWindows()
            print("[INFO] Aplicación cerrada.")

    # ── Despacho de estados ───────────────────────────────────────────────────

    def _dispatch(self, frame: np.ndarray, key: int) -> np.ndarray:
        if self._state == AppState.RECOGNITION:
            return self._state_recognition(frame, key)
        elif self._state == AppState.ADMIN_AUTH:
            return self._state_admin_auth(frame, key)
        elif self._state == AppState.ADMIN_MENU:
            return self._state_admin_menu(frame, key)
        elif self._state == AppState.REGISTER:
            return self._state_register(frame, key)
        elif self._state == AppState.USER_LIST:
            return self._state_user_list(key)
        elif self._state == AppState.USER_EDIT:
            return self._state_user_edit(key)
        elif self._state == AppState.LOG_VIEW:
            return self._state_log_view(key)
        elif self._state == AppState.CAM_SELECT:
            return self._state_cam_select(key)
        return frame.copy()

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: RECONOCIMIENTO
    # ═════════════════════════════════════════════════════════════════════════

    def _state_recognition(self, frame: np.ndarray, key: int) -> np.ndarray:
        # Ctrl+A → admin auth
        if key == 1:
            self._pwd_input  = ""
            self._pwd_error  = False
            self._state = AppState.ADMIN_AUTH
            return frame.copy()

        display = frame.copy()
        self._frame_counter += 1

        if self._frame_counter % self._FRAME_SKIP == 0:
            faces = self._detector.detect(frame)
            self._last_faces = faces

            if faces is None:
                self._last_result = None
            elif len(faces) > 1:
                self._last_result = None   # Señal de múltiples rostros
                self._last_faces  = faces
            else:
                face_info = faces[0]
                try:
                    emb = self._embedder.extract(frame, face_info)
                    result = self._comparator.match(emb)
                    self._last_result = result
                    self._maybe_log_access(result)
                except Exception as e:
                    print(f"[ERROR reconocimiento] {type(e).__name__}: {e}")
                    self._last_result = None

        self._draw_recognition(display)
        return display

    def _maybe_log_access(self, result: MatchResult) -> None:
        """Registra el acceso con cooldown de 5 s por usuario."""
        now = time.time()
        uid = result.user_id if result.is_known else None

        if uid == self._last_access_user_id and (now - self._last_access_log_time) < 5.0:
            return

        self._last_access_user_id  = uid
        self._last_access_log_time = now

        if result.is_known:
            db_manager.log_access(
                status     = "granted",
                confidence = result.confidence,
                user_id    = result.user_id,
                user_name  = result.name,
                department = result.department,
            )
        else:
            db_manager.log_access(
                status     = "unknown",
                confidence = result.confidence,
            )

    def _draw_recognition(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        faces = self._last_faces
        result = self._last_result

        if faces is not None and len(faces) > 1:
            # Múltiples rostros
            semi_transparent_rect(display, (0, 0), (w, h), (50, 50, 80), 0.35)
            put_text_centered(display, i18n.t("multiple_faces"),
                              h // 2 - 20, 22, config.COLOR_YELLOW)
            put_text_centered(display, i18n.t("multiple_faces_msg"),
                              h // 2 + 16, 16, config.COLOR_WHITE)
        elif faces is not None and len(faces) == 1:
            face = faces[0]
            x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])

            if result and result.is_known:
                color = config.COLOR_GREEN
                label = f"{result.name}  {result.confidence:.0f}%"
                status_txt = i18n.t("access_granted")
            else:
                color = config.COLOR_RED
                conf  = result.confidence if result else 0.0
                label = f"{i18n.t('unknown')}  {conf:.0f}%"
                status_txt = i18n.t("access_denied")

            cv2.rectangle(display, (x, y), (x + fw, y + fh), color, 2)

            put_text(display, label, (x, max(0, y - 26)),
                     font_size=16, color=color,
                     bg_color=config.COLOR_DARK, padding=4)

            if result and result.is_known and result.department:
                put_text(display, result.department,
                         (x, y + fh + 6), font_size=14,
                         color=config.COLOR_LIGHT, bg_color=config.COLOR_DARK)

            # Banner de estado en la parte superior
            semi_transparent_rect(display, (0, 0), (w, 36), config.COLOR_DARK, 0.65)
            put_text_centered(display, status_txt, 18, 16, color)

        # Hint inferior
        semi_transparent_rect(display, (0, h - 28), (w, h), config.COLOR_DARK, 0.65)
        put_text(display, i18n.t("hint_admin"), (8, h - 22),
                 font_size=13, color=config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: ADMIN AUTH
    # ═════════════════════════════════════════════════════════════════════════

    def _state_admin_auth(self, frame: np.ndarray, key: int) -> np.ndarray:
        if key == 27:                           # ESC → volver
            self._state = AppState.RECOGNITION
            return frame.copy()
        if key == 13:                           # ENTER → verificar
            digest = hashlib.sha256(self._pwd_input.encode()).hexdigest()
            if digest == config.ADMIN_PASSWORD_HASH:
                self._state     = AppState.ADMIN_MENU
                self._pwd_input = ""
                self._pwd_error = False
            else:
                self._pwd_error      = True
                self._pwd_error_time = time.time()
                self._pwd_input      = ""
        elif key in (8, 127):                   # BACKSPACE
            self._pwd_input = self._pwd_input[:-1]
        elif 32 <= key <= 126:
            self._pwd_input += chr(key)

        display = frame.copy()
        self._draw_admin_auth(display)
        return display

    def _draw_admin_auth(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        bw, bh = 380, 160
        bx = (w - bw) // 2
        by = (h - bh) // 2

        semi_transparent_rect(display, (0, 0), (w, h), config.COLOR_DARK, 0.65)
        semi_transparent_rect(display, (bx, by), (bx + bw, by + bh),
                               (42, 40, 38), 0.92)
        cv2.rectangle(display, (bx, by), (bx + bw, by + bh), config.COLOR_BLUE, 2)

        put_text_centered(display, i18n.t("admin_auth_title"),
                          by + 28, 18, config.COLOR_YELLOW)

        stars = "*" * len(self._pwd_input)
        put_text(display, i18n.t("enter_password") + " " + stars,
                 (bx + 20, by + 68), 16, config.COLOR_WHITE)

        if self._pwd_error and (time.time() - self._pwd_error_time) < 2.5:
            put_text_centered(display, i18n.t("wrong_password"),
                              by + 106, 15, config.COLOR_RED)
        else:
            put_text_centered(display, i18n.t("esc_cancel"),
                              by + 106, 14, config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: MENÚ ADMIN
    # ═════════════════════════════════════════════════════════════════════════

    def _state_admin_menu(self, frame: np.ndarray, key: int) -> np.ndarray:
        if key == 27:                                   # ESC
            self._state = AppState.RECOGNITION
        elif key in (ord('r'), ord('R')):
            self._reg_mgr.reset()
            self._state = AppState.REGISTER
        elif key in (ord('v'), ord('V')):
            self._users = db_manager.get_all_active_users()
            self._user_sel_idx   = 0
            self._user_scroll    = 0
            self._confirm_delete = False
            self._user_msg       = ""
            self._state = AppState.USER_LIST
        elif key in (ord('l'), ord('L')):
            self._logs       = db_manager.get_recent_logs()
            self._log_scroll = 0
            self._state = AppState.LOG_VIEW
        elif key in (ord('c'), ord('C')):
            self._available_cams = CameraManager.detect_available_cameras()
            self._cam_msg        = ""
            self._state = AppState.CAM_SELECT
        elif key in (ord('i'), ord('I')):
            i18n.toggle_language()

        display = frame.copy()
        self._draw_admin_menu(display)
        return display

    def _draw_admin_menu(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        semi_transparent_rect(display, (0, 0), (w, h), config.COLOR_DARK, 0.72)

        put_text_centered(display, i18n.t("admin_menu_title"),
                          44, 22, config.COLOR_YELLOW)

        items = [
            "admin_menu_r",
            "admin_menu_v",
            "admin_menu_l",
            "admin_menu_c",
            "admin_menu_i",
            "admin_menu_esc",
        ]
        line_h = 38
        start_y = 90
        for i, key in enumerate(items):
            color = config.COLOR_LIGHT if i < len(items) - 1 else config.COLOR_GRAY
            put_text_centered(display, i18n.t(key),
                              start_y + i * line_h, 17, color)

        lang = i18n.current_language().upper()
        put_text(display, f"Lang: {lang}  |  Cam: {self._camera.current_index()}",
                 (8, h - 14), 13, config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: REGISTRO
    # ═════════════════════════════════════════════════════════════════════════

    def _state_register(self, frame: np.ndarray, key: int) -> np.ndarray:
        if key == 27:
            self._reg_mgr.reset()
            self._state = AppState.ADMIN_MENU
            return frame.copy()

        sess = self._reg_mgr.session

        if sess.state == RegState.ENTERING_NAME:
            self._reg_mgr.handle_key_name(key)
        elif sess.state == RegState.ENTERING_DEPT:
            self._reg_mgr.handle_key_dept(key)
        elif sess.state == RegState.DUPLICATE_FOUND and key == 27:
            self._reg_mgr.reset()
            self._state = AppState.ADMIN_MENU
            return frame.copy()
        else:
            self._reg_mgr.process_frame(frame)

        # Guardar si corresponde
        if sess.state == RegState.SAVING:
            self._save_new_user()
            return self._blank_frame()

        if sess.state in (RegState.DONE, RegState.CANCELLED):
            self._state = AppState.ADMIN_MENU
            self._reg_mgr.reset()
            return frame.copy()

        display = frame.copy()
        self._draw_registration(display, sess)
        return display

    def _save_new_user(self) -> None:
        sess = self._reg_mgr.session
        uid  = db_manager.add_user(sess.name, sess.department)
        step = max(1, len(sess.embeddings) // 50)
        for emb in sess.embeddings[::step]:
            db_manager.add_embedding(uid, emb, quality_score=1.0)
        # Actualizar caché
        for emb in sess.embeddings[::step]:
            self._comparator.append(uid, sess.name, sess.department, emb)
        sess.state = RegState.DONE

    def _draw_registration(self, display: np.ndarray, sess) -> None:
        h, w = display.shape[:2]

        # Barra de título
        semi_transparent_rect(display, (0, 0), (w, 40), config.COLOR_DARK, 0.80)
        put_text_centered(display, i18n.t("reg_title"), 20, 17, config.COLOR_YELLOW)

        if sess.state == RegState.DUPLICATE_FOUND:
            semi_transparent_rect(display, (0, h // 2 - 50), (w, h // 2 + 50),
                                   config.COLOR_DARK, 0.85)
            put_text_centered(display, i18n.t("reg_duplicate"),
                              h // 2 - 20, 17, config.COLOR_RED)
            put_text_centered(display, sess.duplicate_name or "",
                              h // 2 + 12, 18, config.COLOR_WHITE)
            put_text_centered(display, i18n.t("esc_cancel"),
                              h // 2 + 42, 14, config.COLOR_GRAY)
            return

        if sess.state in (RegState.ENTERING_NAME, RegState.ENTERING_DEPT):
            semi_transparent_rect(display, (0, h // 2 - 80), (w, h // 2 + 80),
                                   config.COLOR_DARK, 0.88)
            if sess.state == RegState.ENTERING_NAME:
                put_text_centered(display, i18n.t("reg_enter_name"),
                                  h // 2 - 40, 17, config.COLOR_LIGHT)
                put_text_centered(display, sess.name_input + "_",
                                  h // 2, 20, config.COLOR_WHITE)
            else:
                put_text_centered(display, i18n.t("reg_enter_dept"),
                                  h // 2 - 40, 17, config.COLOR_LIGHT)
                put_text_centered(display, (sess.dept_input or " ") + "_",
                                  h // 2, 20, config.COLOR_WHITE)
                put_text_centered(display, i18n.t("reg_hint_dept_skip"),
                                  h // 2 + 36, 13, config.COLOR_GRAY)
            put_text_centered(display, i18n.t("reg_enter_confirm") + "  " + i18n.t("esc_cancel"),
                              h // 2 + 62, 14, config.COLOR_GRAY)
            return

        # ── Vista de captura ──────────────────────────────────────────────────
        mvk   = self._reg_mgr.current_movement_key()
        mv_lbl = i18n.t(f"reg_{mvk}") if mvk != "done" else i18n.t("reg_done_capture")

        mv_idx = sess.movement_index
        mv_total = len(config.MOVEMENT_INSTRUCTIONS)
        mv_info = (
            f"{i18n.t('reg_movement')} {min(mv_idx + 1, mv_total)}"
            f"/{mv_total}: {mv_lbl}"
        )

        semi_transparent_rect(display, (0, h - 90), (w, h), config.COLOR_DARK, 0.75)

        # Mensaje de validación
        if sess.validation_msg:
            put_text_centered(display, i18n.t(sess.validation_msg),
                              h - 75, 15, config.COLOR_ORANGE)
        else:
            put_text_centered(display, mv_info, h - 75, 16, config.COLOR_YELLOW)

        # Progreso de capturas
        captures = len(sess.embeddings)
        prog_txt = f"{i18n.t('reg_progress')} {captures}/{config.MIN_EMBEDDINGS_REQUIRED}"
        put_text_centered(display, prog_txt, h - 50, 15, config.COLOR_LIGHT)
        draw_progress_bar(display, 20, h - 32, w - 40, 14,
                          self._reg_mgr.progress_ratio(),
                          color_fill=config.COLOR_GREEN)

        put_text_centered(display, i18n.t("reg_esc_cancel"), h - 10, 13, config.COLOR_GRAY)

        # Dibujar bounding box si hay rostro
        if sess.last_face_info is not None:
            f = sess.last_face_info
            x, y, fw, fh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
            cv2.rectangle(display, (x, y), (x + fw, y + fh), config.COLOR_GREEN, 2)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: LISTA DE USUARIOS
    # ═════════════════════════════════════════════════════════════════════════

    _ROWS_VISIBLE = 10

    def _state_user_list(self, key: int) -> np.ndarray:
        display = self._blank_frame()

        if self._confirm_delete:
            return self._handle_confirm_delete(display, key)

        if key == 27:
            self._state = AppState.ADMIN_MENU
            return display

        # Navegación: flecha arriba o W
        if key in (_KEY_UP, ord('w'), ord('W')):
            self._user_sel_idx = max(0, self._user_sel_idx - 1)
        elif key in (_KEY_DOWN, ord('s'), ord('S')):   # flecha abajo o S
            self._user_sel_idx = min(len(self._users) - 1, self._user_sel_idx + 1)
        elif key in (ord('e'), ord('E')) and self._users:
            u = self._users[self._user_sel_idx]
            self._edit_user     = u
            self._edit_field    = 0
            self._edit_name_buf = u["name"]
            self._edit_dept_buf = u["department"]
            self._state = AppState.USER_EDIT
        elif key in (ord('d'), ord('D')) and self._users:
            self._confirm_delete = True

        # Ajustar scroll
        if self._user_sel_idx < self._user_scroll:
            self._user_scroll = self._user_sel_idx
        elif self._user_sel_idx >= self._user_scroll + self._ROWS_VISIBLE:
            self._user_scroll = self._user_sel_idx - self._ROWS_VISIBLE + 1

        self._draw_user_list(display)
        return display

    def _handle_confirm_delete(self, display: np.ndarray, key: int) -> np.ndarray:
        if key in (ord('s'), ord('S'), ord('y'), ord('Y')):
            uid = self._users[self._user_sel_idx]["id"]
            db_manager.delete_user(uid)
            self._comparator.remove_user(uid)
            self._users = db_manager.get_all_active_users()
            self._user_sel_idx   = min(self._user_sel_idx, max(0, len(self._users) - 1))
            self._confirm_delete = False
            self._user_msg       = i18n.t("users_deleted")
            self._user_msg_time  = time.time()
        elif key in (ord('n'), ord('N'), 27):
            self._confirm_delete = False

        self._draw_user_list(display)
        return display

    def _draw_user_list(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        put_text_centered(display, i18n.t("users_title"), 28, 20, config.COLOR_YELLOW)
        cv2.line(display, (0, 46), (w, 46), config.COLOR_GRAY, 1)

        if not self._users:
            put_text_centered(display, i18n.t("users_no_users"),
                              h // 2, 16, config.COLOR_GRAY)
        else:
            col_id   = 10
            col_name = 60
            col_dept = 280
            col_date = 450
            row_h    = 28
            header_y = 66

            # Encabezados
            for txt, cx in [
                (i18n.t("users_id"),   col_id),
                (i18n.t("users_name"), col_name),
                (i18n.t("users_dept"), col_dept),
                (i18n.t("users_date"), col_date),
            ]:
                put_text(display, txt, (cx, header_y), 14, config.COLOR_GRAY)

            cv2.line(display, (0, header_y + 14), (w, header_y + 14), config.COLOR_GRAY, 1)

            visible = self._users[self._user_scroll: self._user_scroll + self._ROWS_VISIBLE]
            for i, user in enumerate(visible):
                abs_idx = self._user_scroll + i
                ry = header_y + 22 + i * row_h
                is_sel = abs_idx == self._user_sel_idx

                if is_sel:
                    semi_transparent_rect(display, (0, ry - 14), (w, ry + 10),
                                           config.COLOR_BLUE, 0.50)

                color = config.COLOR_WHITE if is_sel else config.COLOR_LIGHT
                date_short = str(user["created_at"])[:10]
                put_text(display, str(user["id"]),         (col_id, ry),   14, color)
                put_text(display, user["name"][:22],       (col_name, ry), 14, color)
                put_text(display, user["department"][:18], (col_dept, ry), 14, color)
                put_text(display, date_short,              (col_date, ry), 14, color)

        # Mensaje temporal
        if self._user_msg and (time.time() - self._user_msg_time) < 2.5:
            put_text_centered(display, self._user_msg, h - 52, 15, config.COLOR_GREEN)

        if self._confirm_delete and self._users:
            name = self._users[self._user_sel_idx]["name"]
            put_text_centered(display,
                              f"{i18n.t('users_confirm_del')} — {name}",
                              h - 52, 15, config.COLOR_RED)

        # Pie
        cv2.line(display, (0, h - 36), (w, h - 36), config.COLOR_GRAY, 1)
        put_text_centered(display, i18n.t("users_nav"),     h - 26, 13, config.COLOR_GRAY)
        put_text_centered(display, i18n.t("users_edit_key"), h - 12, 13, config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: EDICIÓN DE USUARIO
    # ═════════════════════════════════════════════════════════════════════════

    def _state_user_edit(self, key: int) -> np.ndarray:
        display = self._blank_frame()

        if key == 27:
            self._state = AppState.USER_LIST
            return display

        if self._edit_field == 0:           # Editando nombre
            if key == 13:
                self._edit_field = 1
            elif key in (8, 127):
                self._edit_name_buf = self._edit_name_buf[:-1]
            elif 32 <= key <= 126:
                self._edit_name_buf += chr(key)
        else:                               # Editando departamento
            if key == 13:
                # Guardar
                uid  = self._edit_user["id"]
                name = self._edit_name_buf.strip() or self._edit_user["name"]
                dept = self._edit_dept_buf.strip()
                db_manager.update_user(uid, name, dept)
                # Actualizar caché (eliminar entradas antiguas y recargar)
                self._comparator.remove_user(uid)
                for entry in db_manager.load_all_embeddings():
                    if entry["user_id"] == uid:
                        self._comparator.append(uid, name, dept, entry["embedding"])
                self._users = db_manager.get_all_active_users()
                self._user_msg      = i18n.t("users_saved")
                self._user_msg_time = time.time()
                self._state = AppState.USER_LIST
                return display
            elif key in (8, 127):
                self._edit_dept_buf = self._edit_dept_buf[:-1]
            elif 32 <= key <= 126:
                self._edit_dept_buf += chr(key)

        self._draw_user_edit(display)
        return display

    def _draw_user_edit(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        put_text_centered(display, i18n.t("users_edit_title"), 28, 20, config.COLOR_YELLOW)

        fields = [
            (i18n.t("users_name"), self._edit_name_buf),
            (i18n.t("users_dept"), self._edit_dept_buf),
        ]
        for idx, (label, value) in enumerate(fields):
            fy = h // 2 - 40 + idx * 60
            is_active = idx == self._edit_field
            color = config.COLOR_WHITE if is_active else config.COLOR_GRAY
            put_text_centered(display, label, fy - 12, 15, config.COLOR_LIGHT)
            box_text = (value or " ") + ("_" if is_active else "")
            border = config.COLOR_YELLOW if is_active else config.COLOR_GRAY
            cv2.rectangle(display, (w // 2 - 180, fy), (w // 2 + 180, fy + 28), border, 1)
            put_text_centered(display, box_text, fy + 14, 16, color)

        put_text_centered(display,
                          "[ENTER] Siguiente/Guardar  [ESC] Cancelar",
                          h - 20, 13, config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: LOG DE ACCESOS
    # ═════════════════════════════════════════════════════════════════════════

    _LOG_ROWS = 14

    def _state_log_view(self, key: int) -> np.ndarray:
        display = self._blank_frame()

        if key == 27:
            self._state = AppState.ADMIN_MENU
            return display
        if key in (_KEY_UP, ord('w'), ord('W')):
            self._log_scroll = max(0, self._log_scroll - 1)
        elif key in (_KEY_DOWN, ord('s'), ord('S')):
            max_scroll = max(0, len(self._logs) - self._LOG_ROWS)
            self._log_scroll = min(max_scroll, self._log_scroll + 1)

        self._draw_log_view(display)
        return display

    def _draw_log_view(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        put_text_centered(display, i18n.t("log_title"), 28, 20, config.COLOR_YELLOW)
        cv2.line(display, (0, 46), (w, 46), config.COLOR_GRAY, 1)

        if not self._logs:
            put_text_centered(display, i18n.t("log_no_entries"),
                              h // 2, 16, config.COLOR_GRAY)
        else:
            col_time = 6
            col_user = 130
            col_dept = 320
            col_stat = 460
            col_conf = 570
            row_h    = 25
            header_y = 64

            for txt, cx in [
                (i18n.t("log_time"),   col_time),
                (i18n.t("log_user"),   col_user),
                (i18n.t("log_dept"),   col_dept),
                (i18n.t("log_status"), col_stat),
                (i18n.t("log_conf"),   col_conf),
            ]:
                put_text(display, txt, (cx, header_y), 13, config.COLOR_GRAY)

            cv2.line(display, (0, header_y + 12), (w, header_y + 12), config.COLOR_GRAY, 1)

            visible = self._logs[self._log_scroll: self._log_scroll + self._LOG_ROWS]
            for i, log in enumerate(visible):
                ry = header_y + 20 + i * row_h
                ts = str(log["timestamp"])[5:16]    # MM-DD HH:MM

                status = log["status"]
                if status == "granted":
                    scolor = config.COLOR_GREEN
                    slabel = i18n.t("log_granted")
                elif status == "denied":
                    scolor = config.COLOR_ORANGE
                    slabel = i18n.t("log_denied")
                else:
                    scolor = config.COLOR_RED
                    slabel = i18n.t("log_unknown")

                put_text(display, ts,                             (col_time, ry), 13, config.COLOR_LIGHT)
                put_text(display, (log["user_name"] or "-")[:18], (col_user, ry), 13, config.COLOR_LIGHT)
                put_text(display, (log["department"] or "-")[:14],(col_dept, ry), 13, config.COLOR_LIGHT)
                put_text(display, slabel,                         (col_stat, ry), 13, scolor)
                conf_str = f"{log['confidence']:.0f}%" if log["confidence"] else "-"
                put_text(display, conf_str,                       (col_conf, ry), 13, config.COLOR_LIGHT)

        cv2.line(display, (0, h - 24), (w, h - 24), config.COLOR_GRAY, 1)
        put_text_centered(display, i18n.t("log_scroll"), h - 12, 13, config.COLOR_GRAY)

    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO: SELECCIÓN DE CÁMARA
    # ═════════════════════════════════════════════════════════════════════════

    def _state_cam_select(self, key: int) -> np.ndarray:
        display = self._blank_frame()

        if key == 27:
            self._state = AppState.ADMIN_MENU
            return display

        if ord('0') <= key <= ord('9'):
            idx = key - ord('0')
            if idx in self._available_cams:
                ok = self._camera.switch_camera(idx)
                self._cam_msg      = i18n.t("cam_switched") if ok else i18n.t("cam_error")
                self._cam_msg_time = time.time()
                if ok:
                    self._state = AppState.ADMIN_MENU
                    return display

        self._draw_cam_select(display)
        return display

    def _draw_cam_select(self, display: np.ndarray) -> None:
        h, w = display.shape[:2]
        put_text_centered(display, i18n.t("cam_title"), 28, 20, config.COLOR_YELLOW)

        put_text_centered(display, i18n.t("cam_current") + f" {self._camera.current_index()}",
                          70, 15, config.COLOR_LIGHT)

        if not self._available_cams:
            put_text_centered(display, i18n.t("cam_none"), h // 2, 16, config.COLOR_GRAY)
        else:
            put_text_centered(display, i18n.t("cam_found"), 100, 15, config.COLOR_LIGHT)
            for i, idx in enumerate(self._available_cams):
                marker = "►" if idx == self._camera.current_index() else " "
                put_text_centered(display, f"{marker} [{idx}] Camera {idx}",
                                  130 + i * 30, 16, config.COLOR_WHITE)

        if self._cam_msg and (time.time() - self._cam_msg_time) < 2.5:
            put_text_centered(display, self._cam_msg, h - 52, 15, config.COLOR_ORANGE)

        put_text_centered(display, i18n.t("cam_select_hint"), h - 20, 13, config.COLOR_GRAY)

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _blank_frame(self) -> np.ndarray:
        return np.zeros(
            (config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8
        )
