# Restaurante "El Filete" - Sistema de Facturación POS y Menú Digital

Sistema web integral de punto de venta (POS) y menú digital interactivo para el restaurante **"El Filete"**, desarrollado con JavaScript vanilla en el frontend y un backend en Python con base de datos SQLite relacional (`Filete2.db`).

El backend soporta ejecución mediante **Flask** (con CORS activado) y cuenta además con un **modo de respaldo (fallback)** basado en la biblioteca estándar `http.server` de Python, garantizando funcionamiento incluso en entornos donde no se hayan instalado paquetes externos.

---

## Estructura del Proyecto

```text
Proyecto-AED-feature-UI/
├── Facturacion.html      # Interfaz principal del Punto de Venta (POS) e Historial
├── Facturacion.css       # Estilos visuales del POS (soporta temas Claro y Oscuro)
├── MenuFilete.html       # Menú digital público para clientes
├── menu.css              # Estilos del menú público interactivo
├── unificador.html       # Shell contenedor con navegación por iframes entre Menú y POS
├── app.js                # Lógica del frontend (POS, carrito, cálculos, consumo de API)
├── server.py             # Servidor Backend REST (Flask con fallback http.server)
├── init_db.py            # Inicialización de Filete2.db y siembra de catálogo/mesas
├── iniciar.bat           # Script lanzador en 1 clic para Windows con autoverificación
├── optimizar-imagenes.py # Utilidad opcional para comprimir imágenes del menú
├── Filete2.db            # Base de datos SQLite relacional (generada por init_db.py)
├── Imagenes/             # Fotografías de productos y Logo.jpg del restaurante
└── README.md             # Documentación técnica del sistema
```

---

## Base de Datos Relacional (`Filete2.db`)

El sistema implementa integridad referencial completa (`PRAGMA foreign_keys = ON;`) con acciones en cascada (`ON UPDATE CASCADE`, `ON DELETE CASCADE / SET NULL`) e índices de aceleración.

### Tablas y Esquema

1. **`categoria`**:
   - `id_categoria` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `nombre` (TEXT NOT NULL UNIQUE)
   - *Categorías sembradas:* Entradas, Bebida, Mariscos, Cortes, Desayunos, Pollo, Cocteles, Postres, Licores, Cervezas, Sopa, Extras.

2. **`mesa`**:
   - `id_mesa` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `numero_mesa` (INTEGER UNIQUE NOT NULL)
   - `capacidad` (INTEGER NOT NULL)
   - `estado` (TEXT NOT NULL DEFAULT 'Disponible')
   - *Mesas sembradas:* 10 mesas con capacidades de 2, 4, 6, 8 y 12 personas.

3. **`producto`**:
   - `id_producto` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `id_categoria` (INTEGER NOT NULL, FK → `categoria`)
   - `nombre` (TEXT NOT NULL)
   - `descripcion` (TEXT)
   - `precio` (REAL NOT NULL)
   - `imagen_url` (TEXT)
   - `disponible` (INTEGER NOT NULL DEFAULT 1)
   - *Catálogo inicial:* 101 platillos y bebidas con sus imágenes locales asociadas.

4. **`pedido`**:
   - `id_pedido` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `tipo_pedido` (TEXT NOT NULL DEFAULT 'Mesa')
   - `estado` (TEXT NOT NULL DEFAULT 'Pagado')
   - `id_mesa` (INTEGER, FK → `mesa` ON DELETE SET NULL)
   - `total` (REAL NOT NULL)

5. **`detalle_pedido`**:
   - `id_detalle` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `id_pedido` (INTEGER NOT NULL, FK → `pedido` ON DELETE CASCADE)
   - `id_producto` (INTEGER NOT NULL, FK → `producto`)
   - `cantidad` (INTEGER NOT NULL)
   - `precio_unitario` (REAL NOT NULL)
   - `subtotal` (REAL NOT NULL)
   - `observacion` (TEXT)

6. **`factura`**:
   - `id_factura` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `id_pedido` (INTEGER NOT NULL, FK → `pedido` ON DELETE CASCADE)
   - `fecha_hora` (DATETIME DEFAULT CURRENT_TIMESTAMP)
   - `cliente_nombre` (TEXT DEFAULT 'Consumidor Final')
   - `cliente_ruc_cedula` (TEXT)
   - `subtotal` (REAL NOT NULL)
   - `impuesto` (REAL NOT NULL)
   - `descuento` (REAL NOT NULL DEFAULT 0.0)
   - `propina` (REAL NOT NULL DEFAULT 0.0)
   - `monto_total` (REAL NOT NULL)
   - `metodo_pago` (TEXT NOT NULL DEFAULT 'Efectivo')
   - `monto_recibido` (REAL NOT NULL DEFAULT 0.0)
   - `cambio_devuelto` (REAL NOT NULL DEFAULT 0.0)

---

## Endpoints de la API REST (`server.py`)

Todos los endpoints entregan y reciben respuestas en formato `application/json` con cabeceras CORS habilitadas tanto en Flask como en el modo nativo HTTP.

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga el shell unificador (`unificador.html`) o el POS (`Facturacion.html`). |
| `GET` | `/api/categorias` | Lista ordenada de todas las categorías disponibles. |
| `GET` | `/api/productos` | Lista de productos disponibles (`disponible = 1`) con JOIN a categoría. |
| `GET` | `/api/mesas` | Lista de mesas registradas con número, capacidad y estado. |
| `GET` | `/api/facturas` | Historial descendente de facturas emitidas con JOIN a `pedido` y `mesa`. |
| `GET` | `/api/facturas/<id>` | Detalle completo de una factura específica e items vendidos (`detalle_pedido`). |
| `GET` | `/api/facturas/ultimo-id` | Retorna el correlativo del último comprobante emitido (`{"ultimo_id": N}`). |
| `POST`| `/api/ventas` (alias `/api/pedidos`) | Registra transacción atómica (pedido, detalles con subtotal y factura). |

---

## Configuración de Impuestos (IVA)

> [!IMPORTANT]
> **Consistencia de la Tasa de Impuesto:**
> - En el frontend (`app.js`), la tasa está definida mediante la constante `TAX_RATE = 0.15` (15%).
> - En el backend (`server.py`), la tasa está centralizada en la constante `IVA = 0.15` (15%).
> - Si se requiere ajustar el impuesto (por ejemplo, al 18% o 0%), asegúrate de modificar el valor **en ambos archivos simultáneamente** para evitar discrepancias de redondeo entre la previsualización del cajero y el cálculo oficial persistido en la base de datos.

---

## Cómo Ejecutar el Proyecto

### Paso Previo: Inicializar la Base de Datos por Primera Vez

Antes de arrancar el servidor por primera vez (o para restablecer los datos a su estado de fábrica), ejecuta el script de inicialización:

```bash
# Modo interactivo (solicita confirmación si Filete2.db ya existe):
python init_db.py

# Modo forzado (útil para despliegues o scripts automatizados):
python init_db.py --force
```

El script creará las tablas, los índices y sembrará las 12 categorías, 10 mesas y los 101 productos del menú.

---

### Opción 1: En 1 Clic con `iniciar.bat` (Recomendado en Windows)

1. Haz doble clic en el archivo **`iniciar.bat`**.
2. El lanzador realizará automáticamente las siguientes acciones:
   - Detecta la instalación de Python en el sistema (`python`, `py` o rutas `%LOCALAPPDATA%`).
   - Verifica si existe `Filete2.db`. Si no existe, invoca automáticamente `init_db.py --force`.
   - Abre la aplicación en tu navegador predeterminado en `http://localhost:5000`.
   - Inicia el servidor backend (`server.py`).

---

### Opción 2: Ejecución Manual desde la Terminal

1. Abre tu terminal en el directorio del proyecto:
   ```bash
   cd c:\Users\solan\OneDrive\Escritorio\Proyecto-AED-feature-UI
   ```
2. Inicializa la base de datos si aún no lo has hecho:
   ```bash
   python init_db.py --force
   ```
3. Arranca el servidor:
   ```bash
   python server.py
   ```
4. Abre tu navegador web en:
   ```text
   http://localhost:5000
   ```
   Podrás navegar entre el **Menú Digital** y el **Punto de Venta POS** mediante la barra superior.
