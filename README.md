# Sistema de Reconocimiento Facial con Control de Acceso

Sistema **100% local** de reconocimiento facial que detecta e identifica usuarios registrados mediante una cámara web estándar. Sin GPU, sin internet en ejecución, sin servicios en la nube.

> Desarrollado con Python 3.12 + OpenCV (modelos YuNet y SFace ONNX).

---

## Requisitos del sistema

| Componente | Mínimo |
|---|---|
| Sistema operativo | Windows 10/11 (64 bits) |
| Procesador | Intel Core i5 / AMD Ryzen 5 |
| Memoria RAM | 8 GB |
| Cámara | Webcam 720p (USB o integrada) |
| Python | 3.10 – 3.12 |
| Espacio en disco | ~500 MB |

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd "Detector de Rostros python"
```

### 2. Crear entorno virtual e instalar dependencias

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r face_recognition_system/requirements.txt
```

> En Windows puede aparecer el error *"la ejecución de scripts está deshabilitada"*.  
> Solución: ejecuta primero `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

### 3. Descargar los modelos de inteligencia artificial (~40 MB, solo una vez)

```powershell
cd face_recognition_system
python setup_models.py
```

Esto descarga dos modelos ONNX de OpenCV Zoo:
- `face_detection_yunet_2023mar.onnx` — detecta rostros en tiempo real
- `face_recognition_sface_2021dec.onnx` — genera la huella biométrica de 128 dimensiones

---

## Ejecución

```powershell
cd face_recognition_system
python main.py
```

---

## Controles de la aplicación

### Pantalla principal

| Tecla | Acción |
|---|---|
| `Ctrl+A` | Abrir panel de administrador |
| `Q` | Cerrar la aplicación |

### Panel de administrador  
*(contraseña por defecto: `admin123`)*

| Tecla | Acción |
|---|---|
| `R` | Registrar nuevo usuario |
| `V` | Ver lista de usuarios |
| `L` | Ver log de accesos |
| `C` | Cambiar cámara |
| `I` | Cambiar idioma (ES/EN) |
| `ESC` | Volver |

### Navegación en listas

| Tecla | Acción |
|---|---|
| `↑` / `W` | Subir |
| `↓` / `S` | Bajar |
| `E` | Editar usuario |
| `D` | Eliminar usuario |

---

## Ver la base de datos

```powershell
python ver_base_datos.py
```

Menú interactivo con 5 opciones: usuarios, embeddings, log de accesos, búsqueda y estadísticas.

La base de datos SQLite se genera automáticamente en:
```
face_recognition_system/data/database/face_system.db
```

Se puede abrir con cualquier cliente SQLite, por ejemplo [DB Browser for SQLite](https://sqlitebrowser.org/).

---

## Estructura del proyecto

```
face_recognition_system/
├── main.py                  ← Punto de entrada
├── config.py                ← Umbrales, rutas, colores, contraseña admin
├── requirements.txt         ← Dependencias Python
├── setup_models.py          ← Descarga modelos ONNX (ejecutar una vez)
├── ver_base_datos.py        ← Visor interactivo de la BD
│
├── data/                    ← Generado automáticamente (ignorado por git)
│   ├── database/            ← face_system.db
│   ├── models/              ← Modelos ONNX (~40 MB)
│   └── logs/
│
└── app/
    ├── camera/              ← Gestión de webcam
    ├── database/            ← Operaciones SQLite
    ├── recognition/         ← Detección (YuNet) + embeddings (SFace) + comparación
    ├── registration/        ← Máquina de estados del registro
    ├── ui/                  ← Interfaz completa en OpenCV
    └── utils/               ← Texto bilingüe + utilidades de dibujo
```

---

## Configuración avanzada

Edita `config.py` para ajustar el comportamiento:

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `COSINE_THRESHOLD` | `0.40` | Umbral de reconocimiento (↑ más estricto) |
| `MIN_FACE_SIZE` | `60` px | Tamaño mínimo de rostro |
| `PROCESS_EVERY_N_FRAMES` | `5` | Frames salteados (reduce CPU) |
| `DEFAULT_CAMERA_INDEX` | `0` | Índice de cámara |
| `MIN_EMBEDDINGS_REQUIRED` | `50` | Capturas requeridas por registro |

### Cambiar la contraseña de administrador

```python
import hashlib
print(hashlib.sha256("mi_nueva_clave".encode()).hexdigest())
# Pega el resultado en ADMIN_PASSWORD_HASH dentro de config.py
```

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Activa el entorno virtual: `.\venv\Scripts\Activate.ps1` |
| `Modelo no encontrado` | Ejecuta `python setup_models.py` |
| Cámara no abre | Verifica que otra app no la use; cambia `DEFAULT_CAMERA_INDEX` |
| No reconoce el rostro | Registrar con buena iluminación; verificar `COSINE_THRESHOLD` |
| Error al ejecutar scripts en PowerShell | Ejecuta: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |

---

## Tecnologías

| Rol | Tecnología |
|---|---|
| Detección facial | OpenCV YuNet ONNX |
| Reconocimiento facial | OpenCV SFace ONNX (128 dimensiones) |
| Interfaz / cámara | OpenCV 4.13 |
| Texto con tildes | Pillow |
| Base de datos | SQLite3 (incluido en Python) |

**Sin GPU. Sin internet. Sin servicios externos. 100% local.**


---

## Requisitos del sistema

| Componente | Mínimo recomendado |
|---|---|
| Sistema operativo | Windows 10/11 (64 bits) |
| Procesador | Intel Core i5 / AMD Ryzen 5 |
| Memoria RAM | 8 GB |
| Cámara | Webcam 720p (USB o integrada) |
| Python | 3.10 – 3.12 |
| Espacio en disco | ~500 MB (incluye modelos ONNX) |

---

## Instalación

### 1. Crear entorno virtual e instalar dependencias

```powershell
cd "c:\Proyectos Codigos\Detector de Rostros python"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r face_recognition_system\requirements.txt
```

### 2. Descargar modelos ONNX (~40 MB, solo una vez)

```powershell
cd face_recognition_system
python setup_models.py
```

O ejecuta **`descargar_modelos.bat`** con doble clic.

---

## Ejecución

**Doble clic en `iniciar.bat`** (forma recomendada)

O desde terminal:

```powershell
cd "c:\Proyectos Codigos\Detector de Rostros python\face_recognition_system"
..\venv\Scripts\Activate.ps1
python main.py
```

---

## Controles de la aplicación

### Pantalla principal (Reconocimiento)

| Tecla | Acción |
|---|---|
| `Ctrl+A` | Abrir panel de administrador |
| `Q` | Cerrar la aplicación |

### Panel de administrador (contraseña: `admin123`)

| Tecla | Acción |
|---|---|
| `R` | Registrar nuevo usuario |
| `V` | Ver lista de usuarios |
| `L` | Ver log de accesos |
| `C` | Seleccionar cámara |
| `I` | Cambiar idioma (ES/EN) |
| `ESC` | Volver a reconocimiento |

### Registro de usuario

El sistema captura el rostro en **6 posiciones** (centro, izquierda, derecha, arriba, abajo, sonrisa) para obtener mayor robustez. Al finalizar, se pide nombre y departamento.

### Lista de usuarios / Log de accesos

| Tecla | Acción |
|---|---|
| `↑` / `W` | Subir en la lista |
| `↓` / `S` | Bajar en la lista |
| `E` | Editar usuario seleccionado |
| `D` | Eliminar usuario seleccionado |
| `ESC` | Volver al menú |

---

## Ver la base de datos

**Doble clic en `ver_base_datos.bat`** o desde terminal:

```powershell
cd face_recognition_system
python ver_base_datos.py
```

Opciones disponibles:

| Opción | Descripción |
|---|---|
| 1 | Ver todos los usuarios registrados |
| 2 | Ver cantidad de embeddings por usuario |
| 3 | Ver log de accesos con fecha, confianza y estado |
| 4 | Buscar usuario por nombre |
| 5 | Estadísticas generales del sistema |

La base de datos SQLite se encuentra en:
```
face_recognition_system\data\database\face_system.db
```

Se puede abrir directamente con cualquier cliente SQLite (por ejemplo, [DB Browser for SQLite](https://sqlitebrowser.org/)).

### Estructura de tablas

```sql
-- Usuarios registrados
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    department  TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    active      INTEGER DEFAULT 1
);

-- Representaciones faciales (128 dimensiones, modelo SFace)
CREATE TABLE embeddings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE,
    embedding     BLOB NOT NULL,          -- numpy float32 (128,) serializado con pickle
    quality_score REAL DEFAULT 1.0,
    created_at    TEXT DEFAULT (datetime('now','localtime'))
);

-- Registro de accesos
CREATE TABLE access_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    user_name   TEXT,
    department  TEXT,
    timestamp   TEXT DEFAULT (datetime('now','localtime')),
    confidence  REAL DEFAULT 0.0,         -- porcentaje 0–100
    status      TEXT                      -- 'granted' | 'unknown'
);
```

---

## Estructura del proyecto

```
face_recognition_system/
│
├── main.py                  ← Punto de entrada
├── config.py                ← Configuración global (umbrales, rutas, colores)
├── requirements.txt         ← Dependencias Python
├── setup_models.py          ← Descarga modelos ONNX
├── ver_base_datos.py        ← Visor interactivo de la base de datos
│
├── iniciar.bat              ← Lanzador de la aplicación (doble clic)
├── descargar_modelos.bat    ← Descargador de modelos (doble clic)
├── ver_base_datos.bat       ← Visor de BD (doble clic)
│
├── data/
│   ├── database/
│   │   └── face_system.db  ← Base de datos SQLite
│   ├── models/
│   │   ├── face_detection_yunet_2023mar.onnx   ← Detección facial (YuNet)
│   │   └── face_recognition_sface_2021dec.onnx ← Reconocimiento (SFace 128-dim)
│   └── logs/               ← Logs de texto (si aplica)
│
└── app/
    ├── camera/
    │   └── camera_manager.py    ← Gestión de webcam (CAP_DSHOW, multi-cámara)
    ├── database/
    │   └── db_manager.py        ← Todas las operaciones SQLite
    ├── recognition/
    │   ├── face_detector.py     ← Detección con YuNet ONNX
    │   ├── face_embedder.py     ← Embeddings con SFace ONNX
    │   └── face_comparator.py   ← Comparación coseno + caché en RAM
    ├── registration/
    │   └── registration_manager.py  ← Máquina de estados del registro
    ├── ui/
    │   └── main_app.py          ← Interfaz completa en OpenCV
    └── utils/
        ├── i18n.py              ← Cadenas bilingüe ES/EN
        └── image_utils.py       ← Utilidades de dibujo (Pillow + OpenCV)
```

---

## Parámetros configurables

Edita `config.py` para ajustar el comportamiento del sistema:

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `COSINE_THRESHOLD` | `0.40` | Umbral de similitud (↑ más estricto, ↓ más permisivo) |
| `MIN_FACE_SIZE` | `60` px | Tamaño mínimo de rostro para procesar |
| `PROCESS_EVERY_N_FRAMES` | `5` | Procesar 1 de cada N fotogramas (reduce CPU) |
| `DEFAULT_CAMERA_INDEX` | `0` | Índice de cámara predeterminado |
| `MIN_EMBEDDINGS_REQUIRED` | `50` | Mínimo de capturas para completar registro |
| `ADMIN_PASSWORD_HASH` | SHA256 de `admin123` | Hash de la contraseña de administrador |

### Cambiar la contraseña de administrador

```python
import hashlib
nueva = "mi_nueva_clave"
print(hashlib.sha256(nueva.encode()).hexdigest())
# Pega el resultado en ADMIN_PASSWORD_HASH dentro de config.py
```

---

## Tecnologías utilizadas

| Componente | Biblioteca | Versión |
|---|---|---|
| Detección facial | OpenCV YuNet ONNX | `opencv-contrib-python ≥ 4.8` |
| Reconocimiento facial | OpenCV SFace ONNX | `opencv-contrib-python ≥ 4.8` |
| Interfaz / cámara | OpenCV | `4.13` |
| Texto Unicode en frames | Pillow | `≥ 9.0` |
| Base de datos | SQLite3 | integrado en Python |
| Serialización embeddings | pickle + numpy | integrado en Python |

---

## Notas importantes

- **Sin GPU requerida**: todos los modelos corren en CPU mediante OpenCV DNN.
- **Sin internet en ejecución**: los modelos se descargan una sola vez con `setup_models.py`.
- **Privacidad**: todos los datos (imágenes procesadas, embeddings, logs) se almacenan localmente.
- **Capacidad**: el sistema puede manejar hasta ~500 usuarios con buen rendimiento en CPU estándar.
- **Reconocimiento estricto**: el umbral de 0.40 prefiere falsos negativos sobre falsos positivos.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Activar el entorno virtual antes de ejecutar: `..\venv\Scripts\Activate.ps1` |
| `Modelo no encontrado` | Ejecutar `python setup_models.py` o `descargar_modelos.bat` |
| Cámara no abre | Verificar que ninguna otra app use la cámara; cambiar índice en `config.py` |
| No reconoce rostro | Verificar que el registro se hizo con buena iluminación; revisar `COSINE_THRESHOLD` |
| Pantalla negra | Usar `ver_base_datos.py` para verificar que existen usuarios y embeddings en la BD |
