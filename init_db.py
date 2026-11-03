"""
Inicialización de la base de datos SQLite para Restaurante "El Filete".
Crea las tablas, inserta las categorías, mesas, usuarios y el menú completo
conectando cada producto con su imagen correspondiente.
"""

import argparse
import os
import sqlite3
import sys

# Aseguramos que Python encuentre el archivo auth.py en la misma carpeta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import hash_password

# Configuración de la base de datos
DB_NAME = "Filete2.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# ==============================================================================
# DATOS SEMILLA
# ==============================================================================

CATEGORIAS_SEMILLA = [
    "Entradas", "Bebida", "Mariscos", "Cortes", "Desayunos", "Pollo",
    "Cocteles", "Postres", "Licores", "Cervezas", "Sopa", "Extras",
]

MESAS_SEMILLA = [
    (1,  2,  "Disponible"), (2,  2,  "Disponible"), (3,  4,  "Disponible"),
    (4,  4,  "Disponible"), (5,  6,  "Disponible"), (6,  6,  "Disponible"),
    (7,  8,  "Disponible"), (8,  8,  "Disponible"), (9,  10, "Disponible"),
    (10, 4,  "Disponible"),
]

# Formato: (id_producto, id_categoria, nombre, precio, imagen_url)
PRODUCTOS_SEMILLA = [
    # --- ENTRADAS (Categoría 1) ---
    (1, 1, "Tostones con queso", 300, "Imagenes/TostonQ.jpg"),
    (2, 1, "Tostones con carne", 370, "Imagenes/TostonC.jpg"),
    (3, 1, "Tostones mixtos", 370, "Imagenes/TostonMx.jpg"),
    (4, 1, "Consome de camarones", 555, "Imagenes/ConsomeCamarón.jpg"),
    (5, 1, "Canasta de camarones", 555, "Imagenes/CanastaC.jpg"),

    # --- BEBIDAS (Categoría 2) ---
    (6, 2, "Agua Purificada", 65, "Imagenes/Agua.jpg"),
    (7, 2, "Gaseosa/Soda", 65, "Imagenes/Gaseosa.jpg"),
    (8, 2, "Refresco de temporada", 115, "Imagenes/Refrescos.jpg"),
    (9, 2, "Fruit Punch", 150, "Imagenes/Fruit.jpg"),
    (10, 2, "Frozen Fruit", 185, "Imagenes/frozenfruit.jpg"),
    (11, 2, "Gatorade", 70, "Imagenes/Gatorade.jpg"),

    # --- MARISCOS (Categoría 3) ---
    (12, 3, "Camarones al Ajillo", 690, "Imagenes/CamaronesA.jpg"),
    (13, 3, "Camarones Empanizados", 615, "Imagenes/CamaronesE.jpg"),
    (14, 3, "Arroz con Camaron", 615, "Imagenes/ArrozCC.jpg"),
    (15, 3, "Salmon a la plancha", 725, "Imagenes/Salmon.jpg"),
    (16, 3, "Langosta Triton", 1465, "Imagenes/LangostaT.jpg"),
    (17, 3, "Langosta a la Termidor", 1280, "Imagenes/LangostaTe.jpg"),
    (18, 3, "Mar y Tierra", 2205, "Imagenes/MyT.jpg"),
    (19, 3, "Paella Mixta", 1095, "Imagenes/paella-mixta.jpg"),
    (20, 3, "Ceviche de Pescado", 200, "Imagenes/CevicheP.jpg"),
    (21, 3, "Ceviche de Camaron", 220, "Imagenes/CevicheC.jpg"),
    (22, 3, "Ceviche Mixto", 250, "Imagenes/CevicheMx.jpg"),

    # --- CORTES (Categoría 4) ---
    (23, 4, "Filete de Res", 380, "Imagenes/Filete.jpg"),
    (24, 4, "Rib Eye", 380, "Imagenes/RibEye.jpg"),
    (25, 4, "Churrasco Criollo", 300, "Imagenes/Churrasco.jpg"),
    (26, 4, "Lomo de Entraña", 300, "Imagenes/LomoE.jpg"),
    (27, 4, "Puyazo", 300, "Imagenes/puyaso.jpg"),
    (28, 4, "Lomo de Costilla", 570, "Imagenes/LomoC.jpg"),
    (29, 4, "Filete de res con camarones", 450, "Imagenes/FileteCC.jpg"),
    (30, 4, "Arrachera", 350, "Imagenes/Arrachera.jpg"),
    (31, 4, "Filete Jalapeño", 380, "Imagenes/622_02.webp"),
    (32, 4, "Tomahawk", 580, "Imagenes/Tomahawk.jpg"),
    (33, 4, "New York Steak", 350, "Imagenes/NewYorkSteak.jpg"),
    (34, 4, "Poterhouse", 450, "Imagenes/Porterhouse.jpg"),
    (35, 4, "T-Bone", 390, "Imagenes/T-Bone.jpg"),
    (36, 4, "Brocheta", 350, "Imagenes/Brocheta.jpg"),
    (37, 4, "Carne de Asada", 250, "Imagenes/CarneDeAsada.jpg"),
    (38, 4, "Carne Desmenuzada", 220, "Imagenes/CarneDesmenuzada.jpg"),
    (39, 4, "Fajitas de Res", 220, "Imagenes/FajitasDeRes.jpg"),

    # --- DESAYUNOS (Categoría 5) ---
    (40, 5, "Tipico", 250, "Imagenes/Tipico.jpg"),
    (41, 5, "Americano", 300, "Imagenes/Americano.jpg"),
    (42, 5, "Panqueques", 200, "Imagenes/Panqueques.jpg"),
    (43, 5, "Tropical", 200, "Imagenes/Tropical.jpg"),

    # --- POLLO (Categoría 6) ---
    (44, 6, "Pollo Asado", 200, "Imagenes/PolloAsado.jpg"),
    (45, 6, "Pollo Rostizado", 210, "Imagenes/PolloRostizado.jpg"),
    (46, 6, "Fajitas de Pollo", 220, "Imagenes/FajitasDePollo.jpg"),
    (47, 6, "Filete de Pollo", 230, "Imagenes/FileteDePollo.jpg"),
    (48, 6, "Deditos de pollo", 170, "Imagenes/DeditosDePollo.jpg"),
    (49, 6, "Alitas 12u", 275, "Imagenes/Alitas12u.jpg"),
    (50, 6, "Chunk Daiquiri", 290, "Imagenes/ChunkDaiquiri.jpg"),
    (51, 6, "Alitas 18u", 380, "Imagenes/Alitas18u.jpg"),
    (52, 6, "Toston Familiar", 310, "Imagenes/TostonFamiliar.jpg"),

    # --- COCTELES (Categoría 7) ---
    (53, 7, "Margarita", 150, "Imagenes/Margarita.jpg"),
    (54, 7, "Piña Colada", 180, "Imagenes/PiñaColada.jpg"),
    (55, 7, "Martini", 180, "Imagenes/Martini.jpg"),
    (56, 7, "Bloody Mary", 200, "Imagenes/BloodyMary.jpg"),
    (57, 7, "Cuba Libre", 130, "Imagenes/CubaLibre.jpg"),
    (58, 7, "Mojito Cubano", 180, "Imagenes/MojitoCubano.jpg"),
    (59, 7, "Long Islanda Ice Tea", 200, "Imagenes/LongIslandIceTea.jpg"),
    (60, 7, "Mango Daiquiri", 180, "Imagenes/MangoDaiquiri.jpg"),
    (61, 7, "Flor Ginger", 200, "Imagenes/FlorGinger.jpg"),
    (62, 7, "Tom Colins", 180, "Imagenes/TomColins.jpg"),

    # --- POSTRES (Categoría 8) ---
    (63, 8, "Tres Leche", 130, "Imagenes/TresLeche.jpg"),
    (64, 8, "Pio X", 130, "Imagenes/piox.jpg"),
    (65, 8, "Toronjas en Miel", 130, "Imagenes/ToronjasEnMiel.jpg"),
    (66, 8, "Torta de Chocolate", 170, "Imagenes/TortaDeChocolate.jpg"),
    (67, 8, "Selva Negra", 170, "Imagenes/SelvaNegra.jpg"),
    (68, 8, "Cafe", 60, "Imagenes/Cafe.jpg"),
    (69, 8, "Capuchino", 110, "Imagenes/Capuchino.jpg"),

    # --- LICORES (Categoría 9) ---
    (70, 9, "Flor de caña Gran Reserva", 60, "Imagenes/FlorDeCañaGranReserva.jpg"),
    (71, 9, "Flor de caña Extra Lite", 55, "Imagenes/FlorDeCañaExtraLite.jpg"),
    (72, 9, "Flor de caña Centenario", 100, "Imagenes/FlorDeCañaCentenario.jpg"),
    (73, 9, "Tequila Jose Cuervo", 90, "Imagenes/TequilaJoseCuervo.jpg"),
    (74, 9, "Jaggermeister", 120, "Imagenes/Jaggermeister.jpg"),
    (75, 9, "Bailey´s", 100, "Imagenes/Baileys.jpg"),

    # --- CERVEZAS (Categoría 10) ---
    (76, 10, "Toña", 60, "Imagenes/Toña.jpg"),
    (77, 10, "Toña Lite", 60, "Imagenes/ToñaLite.jpg"),
    (78, 10, "Toña Lata", 60, "Imagenes/ToñaLata.jpg"),
    (79, 10, "Victoria Clasica", 60, "Imagenes/VictoriaClasica.jpg"),
    (80, 10, "Victoria Frost", 50, "Imagenes/VictoriaFrost.jpg"),
    (81, 10, "Sol", 100, "Imagenes/Sol.jpg"),
    (82, 10, "Bliss", 110, "Imagenes/Bliss.jpg"),
    (83, 10, "Smirnoff", 110, "Imagenes/Smirnoff.jpg"),
    (84, 10, "Miller Lite", 70, "Imagenes/MillerLite.jpg"),
    (85, 10, "Heineken", 100, "Imagenes/Heineken.jpg"),
    (86, 10, "Bamboo", 70, "Imagenes/Bamboo.jpg"),
    (87, 10, "Adan & Eva", 80, "Imagenes/AdanYEva.jpg"),
    (88, 10, "Hard Seltzer", 65, "Imagenes/HardSeltzer.jpg"),

    # --- SOPAS (Categoría 11) ---
    (89, 11, "Sopa de Pollo", 210, "Imagenes/SopaDePollo.jpg"),
    (90, 11, "Sopa Marinera", 700, "Imagenes/SopaMarinera.jpg"),
    (91, 11, "Sopa Junior Daiquiri", 300, "Imagenes/SopaDeRes.jpg"),
    (92, 11, "Sopa de Res", 250, "Imagenes/SopaDeRes.jpg"),

    # --- EXTRAS (Categoría 12) ---
    (93, 12, "Arroz", 50, "Imagenes/Arroz.jpg"),
    (94, 12, "Frijoles Molidos", 50, "Imagenes/FrijolesMolidos.jpg"),
    (95, 12, "Papas Fritas", 60, "Imagenes/PapasFritas.jpg"),
    (96, 12, "Mayonesa", 40, "Imagenes/Mayonesa.jpg"),
    (97, 12, "Salsa de Tomate", 40, "Imagenes/SalsaDeTomate.jpg"),
    (98, 12, "Tostones 5u", 50, "Imagenes/Tostones.jpg"),
    (99, 12, "Papa Asada 2u", 50, "Imagenes/PapaAsada.jpg"),
    (100, 12, "Galleta", 20, "Imagenes/Galleta.jpg"),
    (101, 12, "Vegetales", 70, "Imagenes/Vegetales.jpg"),
]

# Formato: (username, contraseña_plana, nombre_completo, rol)
USUARIOS_SEMILLA = [
    ("admin",   "admin123",  "Administrador",   "admin"),
    ("cajero1", "cajero123", "Cajero de Turno", "cajero"),
    ("mesero1", "mesero123", "Mesero de Turno", "mesero"),
]

# ==============================================================================
# FUNCIONES DE LA BASE DE DATOS
# ==============================================================================

def _create_schema(cur):
    """Crea todas las tablas e índices en la base de datos."""
    cur.executescript("""
        PRAGMA foreign_keys = ON;

        -- 1. Tablas del Punto de Venta
        CREATE TABLE categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL UNIQUE
        );

        CREATE TABLE producto (
            id_producto  INTEGER PRIMARY KEY AUTOINCREMENT,
            id_categoria INTEGER NOT NULL,
            nombre       TEXT NOT NULL,
            descripcion  TEXT DEFAULT '',
            precio       REAL NOT NULL CHECK (precio >= 0),
            imagen_url   TEXT DEFAULT '',
            disponible   INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria) 
                ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE mesa (
            id_mesa     INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_mesa INTEGER NOT NULL UNIQUE,
            capacidad   INTEGER NOT NULL DEFAULT 4,
            estado      TEXT NOT NULL DEFAULT 'Disponible'
        );

        CREATE TABLE pedido (
            id_pedido   INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_pedido TEXT NOT NULL DEFAULT 'Para Llevar',
            estado      TEXT NOT NULL DEFAULT 'Pagado',
            id_mesa     INTEGER,
            total       REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (id_mesa) REFERENCES mesa(id_mesa) 
                ON UPDATE CASCADE ON DELETE SET NULL
        );

        CREATE TABLE detalle_pedido (
            id_detalle      INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pedido       INTEGER NOT NULL,
            id_producto     INTEGER NOT NULL,
            cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
            precio_unitario REAL NOT NULL,
            subtotal        REAL NOT NULL,
            observacion     TEXT,
            FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (id_producto) REFERENCES producto(id_producto) 
                ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE factura (
            id_factura         INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pedido          INTEGER NOT NULL UNIQUE,
            fecha_hora         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre     TEXT NOT NULL DEFAULT 'Consumidor Final',
            cliente_ruc_cedula TEXT,
            subtotal           REAL NOT NULL DEFAULT 0,
            impuesto           REAL NOT NULL DEFAULT 0,
            descuento          REAL NOT NULL DEFAULT 0,
            propina            REAL NOT NULL DEFAULT 0,
            monto_total        REAL NOT NULL DEFAULT 0,
            metodo_pago        TEXT NOT NULL DEFAULT 'Efectivo',
            monto_recibido     REAL NOT NULL DEFAULT 0,
            cambio_devuelto    REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) 
                ON UPDATE CASCADE ON DELETE CASCADE
        );

        -- 2. Tablas de Seguridad y Reservas
        CREATE TABLE usuario (
            id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol             TEXT NOT NULL CHECK (rol IN ('admin','cajero','mesero')),
            activo          INTEGER NOT NULL DEFAULT 1,
            creado_por      INTEGER,
            fecha_creacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creado_por) REFERENCES usuario(id_usuario) 
                ON UPDATE CASCADE ON DELETE SET NULL
        );

        CREATE UNIQUE INDEX idx_unico_admin 
            ON usuario(rol) WHERE rol = 'admin' AND activo = 1;

        CREATE TABLE sesion (
            id_sesion        INTEGER PRIMARY KEY AUTOINCREMENT,
            token            TEXT NOT NULL UNIQUE,
            id_usuario       INTEGER NOT NULL,
            ip               TEXT,
            user_agent       TEXT,
            fecha_creacion   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_expiracion DATETIME NOT NULL,
            activa           INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) 
                ON UPDATE CASCADE ON DELETE CASCADE
        );

        CREATE TABLE intento_login (
            id_intento INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            ip         TEXT NOT NULL,
            exitoso    INTEGER NOT NULL,
            fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE reserva (
            id_reserva     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente TEXT NOT NULL,
            telefono       TEXT NOT NULL,
            email          TEXT,
            fecha_reserva  DATE NOT NULL,
            hora_reserva   TEXT NOT NULL,
            num_personas   INTEGER NOT NULL CHECK (num_personas > 0),
            id_mesa        INTEGER,
            notas          TEXT,
            estado         TEXT NOT NULL DEFAULT 'pendiente' 
                           CHECK (estado IN ('pendiente','confirmada','cancelada','completada')),
            creado_por     INTEGER,
            fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_mesa) REFERENCES mesa(id_mesa) 
                ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (creado_por) REFERENCES usuario(id_usuario) 
                ON UPDATE CASCADE ON DELETE SET NULL
        );

        CREATE TABLE auditoria (
            id_evento  INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            accion     TEXT NOT NULL,
            entidad    TEXT,
            entidad_id INTEGER,
            detalle    TEXT,
            ip         TEXT,
            fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- 3. Índices de rendimiento
        CREATE INDEX idx_sesion_token        ON sesion(token);
        CREATE INDEX idx_sesion_usuario      ON sesion(id_usuario);
        CREATE INDEX idx_intento_ip_user     ON intento_login(ip, username, fecha_hora);
        CREATE INDEX idx_reserva_fecha       ON reserva(fecha_reserva, hora_reserva);
        CREATE INDEX idx_auditoria_usuario   ON auditoria(id_usuario, fecha_hora);
        CREATE INDEX idx_auditoria_entidad   ON auditoria(entidad, entidad_id);
        CREATE INDEX idx_producto_categoria  ON producto(id_categoria);
        CREATE INDEX idx_detalle_ped_pedido  ON detalle_pedido(id_pedido);
        CREATE INDEX idx_detalle_ped_prod    ON detalle_pedido(id_producto);
        CREATE INDEX idx_pedido_mesa         ON pedido(id_mesa);
        CREATE INDEX idx_factura_fecha       ON factura(fecha_hora);
    """)

def _seed(cur):
    """Inserta los datos iniciales en la base de datos."""
    cur.executemany("INSERT INTO categoria (nombre) VALUES (?)", [(c,) for c in CATEGORIAS_SEMILLA])
    cur.executemany("INSERT INTO mesa (numero_mesa, capacidad, estado) VALUES (?, ?, ?)", MESAS_SEMILLA)
    
    # Insertar productos (ahora incluye la URL de la imagen)
    for p in PRODUCTOS_SEMILLA:
        cur.execute("""
            INSERT INTO producto (id_producto, id_categoria, nombre, precio, imagen_url) 
            VALUES (?, ?, ?, ?, ?)
        """, (p[0], p[1], p[2], p[3], p[4]))

    # Insertar usuarios (con contraseña encriptada)
    for username, password, nombre, rol in USUARIOS_SEMILLA:
        cur.execute("""
            INSERT INTO usuario (username, password_hash, nombre_completo, rol, activo) 
            VALUES (?, ?, ?, ?, 1)
        """, (username, hash_password(password), nombre, rol))


def init_db(force=False):
    """Función principal que orquesta la creación de la base de datos."""
    print("=" * 62)
    print("  RESTAURANTE 'EL FILETE' - INICIALIZACION DE BASE DE DATOS")
    print("=" * 62)

    if os.path.exists(DB_PATH):
        if not force:
            r = input(f"La base de datos '{DB_NAME}' ya existe. ¿Sobrescribirla? [s/N]: ").strip().lower()
            if r not in ("s", "si", "sí", "y", "yes"):
                print("Operación cancelada.")
                return
        os.remove(DB_PATH)
        print(f"Base de datos anterior '{DB_NAME}' eliminada.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    try:
        _create_schema(cur)
        _seed(cur)
        conn.commit()
        print(f"\n¡Base de datos '{DB_NAME}' creada con éxito!")
        print(f"  - {len(CATEGORIAS_SEMILLA)} categorías")
        print(f"  - {len(MESAS_SEMILLA)} mesas")
        print(f"  - {len(PRODUCTOS_SEMILLA)} productos con imágenes")
        print(f"  - {len(USUARIOS_SEMILLA)} usuarios de prueba")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ocurrió un fallo al crear la base de datos: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicializa la base de datos de Restaurante El Filete.")
    parser.add_argument("--force", action="store_true", help="Sobrescribe sin pedir confirmación.")
    args = parser.parse_args()
    init_db(force=args.force)