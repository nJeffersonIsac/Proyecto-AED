import sqlite3
import os

# Nombre de la base de datos
DB_NAME = "restaurante.db"

def init_db():
    print("Inicializando la base de datos...")
    # Si la base de datos ya existe, podemos eliminarla para recrearla limpia
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    # ==========================================
    # 1. CREACIÓN DE TABLAS
    # ==========================================

    # Tabla de Productos (Menú)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY,
        categoria TEXT NOT NULL,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL
    )
    ''')

    # Tabla de Pedidos (Cabecera de la venta)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL,
        estado TEXT DEFAULT 'Pendiente' -- Ej: Pendiente, Pagado, Anulado
    )
    ''')

    # Tabla de Detalles de Pedidos (Los productos dentro de un pedido)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detalle_pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
        FOREIGN KEY (producto_id) REFERENCES productos (id)
    )
    ''')

    # Tabla de Compras de Insumos (Gastos)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compras_insumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        descripcion TEXT NOT NULL,
        costo_total REAL NOT NULL
    )
    ''')

    # ==========================================
    # 2. INSERCIÓN DE DATOS SEMILLA (PRODUCTOS)
    # ==========================================
    
    # Datos extraídos del archivo menuact.pdf
    productos_semilla = [
        (1, 'Entradas', 'Tostones con queso', 300),
        (2, 'Entradas', 'Tostones con carne', 370),
        (3, 'Entradas', 'Tostones mixtos', 370),
        (4, 'Entradas', 'Consome de camarones', 555),
        (5, 'Entradas', 'Canasta de camarones', 555),
        (6, 'Bebida', 'Agua Purificada', 65),
        (7, 'Bebida', 'Gaseosa/Soda', 65),
        (8, 'Bebida', 'Refresco de temporada', 115),
        (9, 'Bebida', 'Fruit Punch', 150),
        (10, 'Bebida', 'Frozen Fruit', 185),
        (11, 'Bebida', 'Gatorade', 70),
        (12, 'Mariscos', 'Camarones al Ajillo', 690),
        (13, 'Mariscos', 'Camarones Empanizados', 615),
        (14, 'Mariscos', 'Arroz con Camaron', 615),
        (15, 'Mariscos', 'Salmon a la plancha', 725),
        (16, 'Mariscos', 'Langosta Triton', 1465),
        (17, 'Mariscos', 'Langosta a la Termidor', 1280),
        (18, 'Mariscos', 'Mar y Tierra', 2205),
        (19, 'Mariscos', 'Paella Mixta', 1095),
        (20, 'Mariscos', 'Ceviche de Pescado', 200),
        (21, 'Mariscos', 'Ceviche de Camaron', 220),
        (22, 'Mariscos', 'Ceviche Mixto', 250),
        (23, 'Cortes', 'Filete de Res', 380),
        (24, 'Cortes', 'Rib Eye', 380),
        (25, 'Cortes', 'Churrasco Criollo', 300),
        (26, 'Cortes', 'Lomo de Entraña', 300),
        (27, 'Cortes', 'Puyazo', 300),
        (28, 'Cortes', 'Lomo de Costilla', 570),
        (29, 'Cortes', 'Filete de res con camarones', 450),
        (30, 'Cortes', 'Arrachera', 350),
        (31, 'Cortes', 'Filete Jalapeño', 380),
        (32, 'Cortes', 'Tomahawk', 580),
        (33, 'Cortes', 'New York Steak', 350),
        (34, 'Cortes', 'Poterhouse', 450),
        (35, 'Cortes', 'T-Bone', 390),
        (36, 'Cortes', 'Brocheta', 350),
        (37, 'Cortes', 'Carne de Asada', 250),
        (38, 'Cortes', 'Carne Desmenuzada', 220),
        (39, 'Cortes', 'Fajitas de Res', 220),
        (40, 'Desayunos', 'Tipico', 250),
        (41, 'Desayunos', 'Americano', 300),
        (42, 'Desayunos', 'Panqueques', 200),
        (43, 'Desayunos', 'Tropical', 200),
        (44, 'Pollo', 'Pollo Asado', 200),
        (45, 'Pollo', 'Pollo Rostizado', 210),
        (46, 'Pollo', 'Fajitas de Pollo', 220),
        (47, 'Pollo', 'Filete de Pollo', 230),
        (48, 'Pollo', 'Deditos de pollo', 170),
        (49, 'Pollo', 'Alitas 12u', 275),
        (50, 'Pollo', 'Chunk Daiquiri', 290),
        (51, 'Pollo', 'Alitas 18u', 380),
        (52, 'Pollo', 'Toston Familiar', 310),
        (53, 'Cocteles', 'Margarita', 150),
        (54, 'Cocteles', 'Piña Colada', 180),
        (55, 'Cocteles', 'Martini', 180),
        (56, 'Cocteles', 'Bloody Mary', 200),
        (57, 'Cocteles', 'Cuba Libre', 130),
        (58, 'Cocteles', 'Mojito Cubano', 180),
        (59, 'Cocteles', 'Long Islanda Ice Tea', 200),
        (60, 'Cocteles', 'Mango Daiquiri', 180),
        (61, 'Cocteles', 'Flor Ginger', 200),
        (62, 'Cocteles', 'Tom Colins', 180),
        (63, 'Postres', 'Tres Leche', 130),
        (64, 'Postres', 'Pio X', 130),
        (65, 'Postres', 'Toronjas en Miel', 130),
        (66, 'Postres', 'Torta de Chocolate', 170),
        (67, 'Postres', 'Selva Negra', 170),
        (68, 'Postres', 'Cafe', 60),
        (69, 'Postres', 'Capuchino', 110),
        (70, 'Licores', 'Flor de caña Gran Reserva', 60),
        (71, 'Licores', 'Flor de caña Extra Lite', 55),
        (72, 'Licores', 'Flor de caña Centenario', 100),
        (73, 'Licores', 'Tequila Jose Cuervo', 90),
        (74, 'Licores', 'Jaggermeister', 120),
        (75, 'Licores', 'Bailey´s', 100),
        (76, 'Cervezas', 'Toña', 60),
        (77, 'Cervezas', 'Toña Lite', 60),
        (78, 'Cervezas', 'Toña Lata', 60),
        (79, 'Cervezas', 'Victoria Clasica', 60),
        (80, 'Cervezas', 'Victoria Frost', 50),
        (81, 'Cervezas', 'Sol', 100),
        (82, 'Cervezas', 'Bliss', 110),
        (83, 'Cervezas', 'Smirnoff', 110),
        (84, 'Cervezas', 'Miller Lite', 70),
        (85, 'Cervezas', 'Heineken', 100),
        (86, 'Cervezas', 'Bamboo', 70),
        (87, 'Cervezas', 'Adan & Eva', 80),
        (88, 'Cervezas', 'Hard Seltzer', 65),
        (89, 'Sopa', 'Sopa de Pollo', 210),
        (90, 'Sopa', 'Sopa Marinera', 700),
        (91, 'Sopa', 'Sopa Junior Daiquiri', 300),
        (92, 'Sopa', 'Sopa de Res', 250),
        (93, 'Extras', 'Arroz', 50),
        (94, 'Extras', 'Frijoles Molidos', 50),
        (95, 'Extras', 'Papas Fritas', 60),
        (96, 'Extras', 'Mayonesa', 40),
        (97, 'Extras', 'Salsa de Tomate', 40),
        (98, 'Extras', 'Tostones 5u', 50),
        (99, 'Extras', 'Papa Asada 2u', 50),
        (100, 'Extras', 'Galleta', 20),
        (101, 'Extras', 'Vegetales', 70)
    ]

    cursor.executemany('''
    INSERT INTO productos (id, categoria, nombre, precio)
    VALUES (?, ?, ?, ?)
    ''', productos_semilla)

    # Guardar cambios y cerrar conexión
    conexion.commit()
    conexion.close()
    print(f"Base de datos '{DB_NAME}' creada con éxito.")
    print(f"Se insertaron {len(productos_semilla)} productos en el menú.")

if __name__ == '__main__':
    init_db()
