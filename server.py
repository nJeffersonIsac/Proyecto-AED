"""
Servidor Backend para Restaurante "El Filete"
Conecta con Filete2.db (SQLite con soporte relacional completo).
Soporta Flask y modo de respaldo con servidor HTTP nativo de Python.
"""
import os
import sys
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "Filete2.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

def get_db():
    """Retorna una conexión a la base de datos con llaves foráneas activadas."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de datos {DB_NAME} no encontrada en {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

# ==============================================================================
# 1. IMPLEMENTACIÓN CON FLASK
# ==============================================================================
try:
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS

    app = Flask(__name__, static_folder=BASE_DIR)
    CORS(app)

    @app.route('/')
    def index():
        if os.path.exists(os.path.join(BASE_DIR, 'unificador.html')):
            return send_from_directory(BASE_DIR, 'unificador.html')
        return send_from_directory(BASE_DIR, 'Facturacion.html')

    @app.route('/<path:path>')
    def static_files(path):
        if os.path.exists(os.path.join(BASE_DIR, path)):
            return send_from_directory(BASE_DIR, path)
        return send_from_directory(BASE_DIR, 'unificador.html')

    @app.route('/api/categorias', methods=['GET'])
    def api_categorias():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id_categoria, nombre FROM categoria ORDER BY id_categoria ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(rows)

    @app.route('/api/productos', methods=['GET'])
    def api_productos():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id_producto,
                p.nombre,
                p.descripcion,
                p.precio,
                p.imagen_url,
                p.disponible,
                c.id_categoria,
                c.nombre AS categoria
            FROM producto p
            JOIN categoria c ON p.id_categoria = c.id_categoria
            WHERE p.disponible = 1
            ORDER BY c.id_categoria ASC, p.id_producto ASC
        """)
        productos = [
            {
                "id_producto": r["id_producto"],
                "nombre": r["nombre"],
                "descripcion": r["descripcion"] or "",
                "precio": float(r["precio"]),
                "imagen_url": r["imagen_url"] or "",
                "disponible": r["disponible"],
                "id_categoria": r["id_categoria"],
                "categoria": r["categoria"]
            }
            for r in cursor.fetchall()
        ]
        conn.close()
        return jsonify(productos)

    @app.route('/api/mesas', methods=['GET'])
    def api_mesas():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id_mesa, numero_mesa, capacidad, estado FROM mesa ORDER BY numero_mesa ASC")
        mesas = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(mesas)

    @app.route('/api/facturas', methods=['GET'])
    def api_facturas_list():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                f.id_factura,
                f.id_pedido,
                f.fecha_hora,
                f.cliente_nombre,
                f.cliente_ruc_cedula,
                f.subtotal,
                f.impuesto,
                f.descuento,
                f.propina,
                f.monto_total,
                f.metodo_pago,
                f.monto_recibido,
                f.cambio_devuelto,
                p.tipo_pedido,
                p.id_mesa,
                m.numero_mesa
            FROM factura f
            JOIN pedido p ON f.id_pedido = p.id_pedido
            LEFT JOIN mesa m ON p.id_mesa = m.id_mesa
            ORDER BY f.id_factura DESC
        """)
        facturas = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(facturas)

    @app.route('/api/facturas/<int:id_factura>', methods=['GET'])
    def api_factura_detalle(id_factura):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                f.id_factura,
                f.id_pedido,
                f.fecha_hora,
                f.cliente_nombre,
                f.cliente_ruc_cedula,
                f.subtotal,
                f.impuesto,
                f.descuento,
                f.propina,
                f.monto_total,
                f.metodo_pago,
                f.monto_recibido,
                f.cambio_devuelto,
                p.tipo_pedido,
                p.id_mesa,
                m.numero_mesa
            FROM factura f
            JOIN pedido p ON f.id_pedido = p.id_pedido
            LEFT JOIN mesa m ON p.id_mesa = m.id_mesa
            WHERE f.id_factura = ?
        """, (id_factura,))
        factura_row = cursor.fetchone()
        
        if not factura_row:
            conn.close()
            return jsonify({"error": f"Factura #{id_factura} no encontrada"}), 404

        factura = dict(factura_row)

        cursor.execute("""
            SELECT 
                dp.id_detalle,
                dp.id_producto,
                pr.nombre,
                dp.cantidad,
                dp.precio_unitario,
                dp.subtotal,
                dp.observacion
            FROM detalle_pedido dp
            JOIN producto pr ON dp.id_producto = pr.id_producto
            WHERE dp.id_pedido = ?
            ORDER BY dp.id_detalle ASC
        """, (factura["id_pedido"],))
        
        factura["items"] = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(factura)

    @app.route('/api/facturas/ultimo-id', methods=['GET'])
    def api_ultimo_id():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(id_factura), 0) AS ultimo_id FROM factura")
        row = cursor.fetchone()
        conn.close()
        return jsonify({"ultimo_id": row["ultimo_id"]})

    @app.route('/api/ventas', methods=['POST'])
    @app.route('/api/pedidos', methods=['POST'])
    def api_crear_venta():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Cuerpo de solicitud inválido o JSON vacío"}), 400

        items = data.get('items', [])
        if not items:
            return jsonify({"error": "La orden no contiene productos"}), 400

        id_mesa = data.get('id_mesa')
        tipo_pedido = data.get('tipo_pedido', 'Mesa' if id_mesa else 'Para Llevar')
        cliente_nombre = data.get('cliente_nombre', 'Consumidor Final') or 'Consumidor Final'
        cliente_ruc_cedula = data.get('cliente_ruc_cedula')
        metodo_pago = data.get('metodo_pago', 'Efectivo')
        descuento = float(data.get('descuento', 0))
        propina = float(data.get('propina', 0))
        monto_recibido = float(data.get('monto_recibido', 0))

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Validar y calcular precios a partir de la DB (seguridad de precios)
            subtotal = 0.0
            items_procesados = []

            for it in items:
                prod_id = int(it.get('id_producto'))
                cantidad = int(it.get('cantidad', 1))
                if cantidad <= 0:
                    continue

                cursor.execute("SELECT id_producto, nombre, precio FROM producto WHERE id_producto = ?", (prod_id,))
                prod = cursor.fetchone()
                if not prod:
                    raise ValueError(f"Producto con ID {prod_id} no existe.")

                precio_unitario = float(prod['precio'])
                item_subtotal = round(precio_unitario * cantidad, 2)
                subtotal += item_subtotal

                items_procesados.append({
                    "id_producto": prod_id,
                    "nombre": prod['nombre'],
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "subtotal": item_subtotal,
                    "observacion": it.get('observacion')
                })

            subtotal = round(subtotal, 2)
            impuesto = round(subtotal * 0.15, 2) # 15% IVA
            monto_total = round(subtotal + impuesto + propina - descuento, 2)
            cambio_devuelto = round(max(0, monto_recibido - monto_total), 2) if monto_recibido > 0 else 0.0

            # 2. Insertar Pedido
            cursor.execute("""
                INSERT INTO pedido (tipo_pedido, estado, id_mesa, total)
                VALUES (?, 'Pagado', ?, ?)
            """, (tipo_pedido, id_mesa, monto_total))
            id_pedido = cursor.lastrowid

            # 3. Insertar Detalles de Pedido (congelando precio)
            for it in items_procesados:
                cursor.execute("""
                    INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, observacion)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_pedido, it['id_producto'], it['cantidad'], it['precio_unitario'], it['observacion']))

            # 4. Insertar Factura
            cursor.execute("""
                INSERT INTO factura (
                    id_pedido, cliente_nombre, cliente_ruc_cedula,
                    subtotal, impuesto, descuento, propina,
                    monto_total, metodo_pago, monto_recibido, cambio_devuelto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_pedido, cliente_nombre, cliente_ruc_cedula,
                subtotal, impuesto, descuento, propina,
                monto_total, metodo_pago, monto_recibido, cambio_devuelto
            ))
            id_factura = cursor.lastrowid

            conn.commit()

            return jsonify({
                "status": "success",
                "id_factura": id_factura,
                "id_pedido": id_pedido,
                "subtotal": subtotal,
                "impuesto": impuesto,
                "monto_total": monto_total,
                "metodo_pago": metodo_pago,
                "cambio_devuelto": cambio_devuelto,
                "mensaje": f"Factura #{id_factura:06d} generada exitosamente"
            }), 201

        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    def run_server(port=5000):
        print("=" * 65)
        print("    RESTAURANTE 'EL FILETE' - SERVIDOR BACKEND (FLASK)")
        print("=" * 65)
        print(f" -> Base de datos conectada : {DB_NAME}")
        print(f" -> Servidor disponible en  : http://localhost:{port}")
        print(" -> Presiona CTRL + C para detener.")
        print("=" * 65)
        app.run(host='0.0.0.0', port=port, debug=False)

except ImportError:
    # ==============================================================================
    # 2. MODO RESPALDO (Sin dependencias externas, usando http.server de Python)
    # ==============================================================================
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    from urllib.parse import urlparse

    class FallbackHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=BASE_DIR, **kwargs)

        def _send_cors(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        def _send_json(self, status, obj):
            payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._send_cors()
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_OPTIONS(self):
            self.send_response(200)
            self._send_cors()
            self.end_headers()

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == '/' or path == '/index.html':
                self.path = '/unificador.html'
                return super().do_GET()

            if path == '/api/categorias':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT id_categoria, nombre FROM categoria ORDER BY id_categoria ASC")
                data = [dict(r) for r in cur.fetchall()]
                conn.close()
                return self._send_json(200, data)

            elif path == '/api/productos':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.imagen_url, p.disponible, c.id_categoria, c.nombre AS categoria
                    FROM producto p
                    JOIN categoria c ON p.id_categoria = c.id_categoria
                    WHERE p.disponible = 1
                    ORDER BY c.id_categoria ASC, p.id_producto ASC
                """)
                data = [
                    {
                        "id_producto": r["id_producto"],
                        "nombre": r["nombre"],
                        "descripcion": r["descripcion"] or "",
                        "precio": float(r["precio"]),
                        "imagen_url": r["imagen_url"] or "",
                        "disponible": r["disponible"],
                        "id_categoria": r["id_categoria"],
                        "categoria": r["categoria"]
                    }
                    for r in cur.fetchall()
                ]
                conn.close()
                return self._send_json(200, data)

            elif path == '/api/mesas':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT id_mesa, numero_mesa, capacidad, estado FROM mesa ORDER BY numero_mesa ASC")
                data = [dict(r) for r in cur.fetchall()]
                conn.close()
                return self._send_json(200, data)

            elif path == '/api/facturas':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    SELECT f.id_factura, f.id_pedido, f.fecha_hora, f.cliente_nombre, f.cliente_ruc_cedula,
                           f.subtotal, f.impuesto, f.descuento, f.propina, f.monto_total, f.metodo_pago,
                           f.monto_recibido, f.cambio_devuelto, p.tipo_pedido, p.id_mesa, m.numero_mesa
                    FROM factura f
                    JOIN pedido p ON f.id_pedido = p.id_pedido
                    LEFT JOIN mesa m ON p.id_mesa = m.id_mesa
                    ORDER BY f.id_factura DESC
                """)
                data = [dict(r) for r in cur.fetchall()]
                conn.close()
                return self._send_json(200, data)

            elif path == '/api/facturas/ultimo-id':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT COALESCE(MAX(id_factura), 0) AS ultimo_id FROM factura")
                row = cur.fetchone()
                conn.close()
                return self._send_json(200, {"ultimo_id": row["ultimo_id"]})

            elif path.startswith('/api/facturas/'):
                try:
                    fact_id = int(path.split('/')[-1])
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM factura WHERE id_factura = ?", (fact_id,))
                    frow = cur.fetchone()
                    if not frow:
                        conn.close()
                        return self._send_json(404, {"error": "No encontrada"})
                    factura = dict(frow)
                    cur.execute("""
                        SELECT dp.*, pr.nombre FROM detalle_pedido dp
                        JOIN producto pr ON dp.id_producto = pr.id_producto
                        WHERE dp.id_pedido = ?
                    """, (factura['id_pedido'],))
                    factura['items'] = [dict(r) for r in cur.fetchall()]
                    conn.close()
                    return self._send_json(200, factura)
                except Exception as e:
                    return self._send_json(500, {"error": str(e)})

            else:
                return super().do_GET()

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path in ['/api/ventas', '/api/pedidos']:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body.decode('utf-8'))
                    items = data.get('items', [])
                    if not items:
                        return self._send_json(400, {"error": "Sin productos"})

                    id_mesa = data.get('id_mesa')
                    tipo_pedido = data.get('tipo_pedido', 'Mesa' if id_mesa else 'Para Llevar')
                    cliente_nombre = data.get('cliente_nombre', 'Consumidor Final') or 'Consumidor Final'
                    cliente_ruc_cedula = data.get('cliente_ruc_cedula')
                    metodo_pago = data.get('metodo_pago', 'Efectivo')
                    descuento = float(data.get('descuento', 0))
                    propina = float(data.get('propina', 0))
                    monto_recibido = float(data.get('monto_recibido', 0))

                    conn = get_db()
                    cur = conn.cursor()

                    subtotal = 0.0
                    items_procesados = []
                    for it in items:
                        pid = int(it.get('id_producto'))
                        cant = int(it.get('cantidad', 1))
                        cur.execute("SELECT precio, nombre FROM producto WHERE id_producto = ?", (pid,))
                        p = cur.fetchone()
                        if not p:
                            raise ValueError(f"Producto {pid} no existe")
                        pu = float(p['precio'])
                        st = round(pu * cant, 2)
                        subtotal += st
                        items_procesados.append((pid, cant, pu, it.get('observacion')))

                    subtotal = round(subtotal, 2)
                    impuesto = round(subtotal * 0.15, 2)
                    monto_total = round(subtotal + impuesto + propina - descuento, 2)
                    cambio = round(max(0, monto_recibido - monto_total), 2) if monto_recibido > 0 else 0.0

                    cur.execute("INSERT INTO pedido (tipo_pedido, estado, id_mesa, total) VALUES (?, 'Pagado', ?, ?)", (tipo_pedido, id_mesa, monto_total))
                    id_pedido = cur.lastrowid

                    for it in items_procesados:
                        cur.execute("INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, observacion) VALUES (?, ?, ?, ?, ?)", (id_pedido, it[0], it[1], it[2], it[3]))

                    cur.execute("""
                        INSERT INTO factura (id_pedido, cliente_nombre, cliente_ruc_cedula, subtotal, impuesto, descuento, propina, monto_total, metodo_pago, monto_recibido, cambio_devuelto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id_pedido, cliente_nombre, cliente_ruc_cedula, subtotal, impuesto, descuento, propina, monto_total, metodo_pago, monto_recibido, cambio))
                    id_factura = cur.lastrowid

                    conn.commit()
                    conn.close()

                    return self._send_json(201, {
                        "status": "success",
                        "id_factura": id_factura,
                        "id_pedido": id_pedido,
                        "monto_total": monto_total,
                        "mensaje": f"Factura #{id_factura:06d} generada exitosamente"
                    })
                except Exception as e:
                    return self._send_json(500, {"error": str(e)})
            else:
                self.send_error(404, "Not Found")

    def run_server(port=5000):
        print("=" * 65)
        print(" RESTAURANTE 'EL FILETE' - SERVIDOR BACKEND (ESTANDAR)")
        print("=" * 65)
        print(f" -> Base de datos conectada : {DB_NAME}")
        print(f" -> Servidor disponible en  : http://localhost:{port}")
        print(" -> Presiona CTRL + C para detener.")
        print("=" * 65)
        httpd = ThreadingHTTPServer(('0.0.0.0', port), FallbackHandler)
        httpd.serve_forever()

if __name__ == '__main__':
    puerto = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        puerto = int(sys.argv[1])

    try:
        run_server(port=puerto)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor detenido por el usuario.")