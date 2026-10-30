# Restaurante "El Filete" - (Punto de Venta)

Sistema web completo de punto de venta y gestión de pedidos para el restaurante **El Filete**, conectado a un backend en Python con base de datos SQLite y servido mediante Flask (con modo de respaldo nativo sin librerías externas).

---

## Estructura del Proyecto

```text
AED/
├── index.html           # Interfaz gráfica principal del POS
├── styles.css           # Estilos visuales modernos
├── app.js               # Lógica del frontend conectada a la API
├── server.py            # Servidor Backend (Flask + SQLite)
├── init_db.py           # Script de inicialización de la base de datos
├── restaurante.db       # Base de datos SQLite
├── requirements.txt     # Dependencias de Python (Flask, Flask-Cors)
├── iniciar.bat          # Acceso directo para ejecutar todo en 1 clic
├── .vscode/             # Configuración para Visual Studio Code
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json


---

## Cómo Correr Todo Junto

Tienes 3 formas sencillas de ejecutar el proyecto:

### Opción 1: En 1 Clic (Recomendado para Cualquier Usuario)
1. Haz doble clic en el archivo **`iniciar.bat`**.
2. El script verificará Python, creará la base de datos si no existe, iniciará el servidor backend y abrirá automáticamente tu navegador web en `http://localhost:5000`.

---

### Opción 2: Desde Visual Studio Code
1. Abre **Visual Studio Code**.
2. Ve a **Archivo > Abrir carpeta...** (`File > Open Folder...`) y selecciona esta carpeta del proyecto.
3. Puedes ejecutarlo de cualquiera de estas formas:
   - **Forma rápida:** Abre el archivo `server.py` y haz clic en el botón de **Play / Ejecutar archivo de Python** (arriba a la derecha).
   - **Con depurador:** Presiona la tecla **`F5`** (o ve a la pestaña *Ejecutar y depurar* y haz clic en *Iniciar Servidor (El Filete)*).
   - **Desde la terminal integrada de VS Code:** Abre la terminal (`Ctrl + ñ`) y escribe:
     ```bash
     python server.py
     ```
4. Abre tu navegador web en: **`http://localhost:5000`**.

---

## Conexión Frontend - Backend (API REST)

El frontend (`app.js`) se comunica automáticamente con los siguientes endpoints del backend (`server.py`):

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga la página principal del punto de venta (`index.html`). |
| `GET` | `/api/productos` | Obtiene los 101 productos del menú desde la tabla `productos` en SQLite. |
| `GET` | `/api/pedidos/ultimo-id` | Obtiene el último número de comprobante registrado para calcular el siguiente correlativo de factura (`000001`, `000002`, ...). |
| `GET` | `/api/pedidos` | Lista el historial de pedidos y ventas registradas. |
| `POST` | `/api/pedidos` | Guarda una nueva venta en la tabla `pedidos` y cada uno de sus productos en `detalle_pedidos`. |

---

## Base de Datos SQLite (`restaurante.db`)

El sistema utiliza las siguientes tablas creadas por `init_db.py`:
- **`productos`**: Almacena ID, categoría, nombre y precio de cada producto del menú.
- **`pedidos`**: Cabecera de la factura (ID correlativo, fecha/hora, total y estado/método de pago).
- **`detalle_pedidos`**: Detalle de cada producto vendido por pedido (pedido_id, producto_id, cantidad, subtotal).

