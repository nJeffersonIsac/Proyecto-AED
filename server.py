"""
Servidor Backend para Restaurante "El Filete".
Auth, roles, reportes y reservas. Compatible Flask + fallback http.server.
"""
import os
import sys
import json
import hmac
import sqlite3
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from auth import (
    get_db, hash_password, verify_password, generar_token,
    crear_sesion, validar_sesion, renovar_sesion_si_pronto_expira,
    invalidar_sesion, invalidar_sesiones_usuario, limpiar_sesiones_expiradas,
    registrar_intento, contar_intentos_fallidos, registrar_auditoria,
)

DB_NAME = "Filete2.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)
IVA = 0.15


def _core_crear_venta(conn, data):
    items = data.get('items', [])
    if not items:
        raise ValueError("La orden no contiene productos")

    id_mesa = data.get('id_mesa')
    tipo_pedido = data.get('tipo_pedido', 'Mesa' if id_mesa else 'Para Llevar')
    cliente_nombre = data.get('cliente_nombre') or 'Consumidor Final'
    cliente_ruc = data.get('cliente_ruc_cedula')
    metodo_pago = data.get('metodo_pago', 'Efectivo')
    descuento = float(data.get('descuento', 0) or 0)
    propina = float(data.get('propina', 0) or 0)
    monto_recibido = float(data.get('monto_recibido', 0) or 0)

    cur = conn.cursor()
    subtotal = 0.0
    procesados = []
    for it in items:
        pid = int(it.get('id_producto'))
        cant = int(it.get('cantidad', 1))
        if cant <= 0:
            continue
        cur.execute("SELECT nombre, precio FROM producto WHERE id_producto = ?", (pid,))
        p = cur.fetchone()
        if not p:
            raise ValueError(f"Producto con ID {pid} no existe")
        pu = float(p['precio'])
        st = round(pu * cant, 2)
        subtotal += st
        procesados.append((pid, cant, pu, st, it.get('observacion')))

    subtotal = round(subtotal, 2)
    impuesto = round(subtotal * IVA, 2)
    monto_total = round(subtotal + impuesto + propina - descuento, 2)
    cambio = round(max(0.0, monto_recibido - monto_total), 2) if monto_recibido > 0 else 0.0

    try:
        cur.execute("INSERT INTO pedido (tipo_pedido, estado, id_mesa, total) VALUES (?, 'Pagado', ?, ?)",
                    (tipo_pedido, id_mesa, monto_total))
        id_pedido = cur.lastrowid
        for pid, cant, pu, st, obs in procesados:
            cur.execute("""INSERT INTO detalle_pedido
                           (id_pedido, id_producto, cantidad, precio_unitario, subtotal, observacion)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (id_pedido, pid, cant, pu, st, obs))
        cur.execute("""INSERT INTO factura
                       (id_pedido, cliente_nombre, cliente_ruc_cedula, subtotal, impuesto,
                        descuento, propina, monto_total, metodo_pago, monto_recibido, cambio_devuelto)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id_pedido, cliente_nombre, cliente_ruc, subtotal, impuesto,
                     descuento, propina, monto_total, metodo_pago, monto_recibido, cambio))
        id_factura = cur.lastrowid
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return {
        "status": "success", "id_factura": id_factura, "id_pedido": id_pedido,
        "subtotal": subtotal, "impuesto": impuesto, "monto_total": monto_total,
        "metodo_pago": metodo_pago, "cambio_devuelto": cambio,
        "mensaje": f"Factura #{id_factura:06d} generada exitosamente",
    }


def _core_eliminar_factura(conn, id_factura, id_usuario, ip):
    cur = conn.cursor()
    cur.execute("SELECT id_pedido, monto_total FROM factura WHERE id_factura = ?", (id_factura,))
    row = cur.fetchone()
    if not row:
        raise LookupError("Factura no encontrada")
    id_pedido = row['id_pedido']
    monto = row['monto_total']
    try:
        cur.execute("DELETE FROM factura WHERE id_factura = ?", (id_factura,))
        cur.execute("DELETE FROM detalle_pedido WHERE id_pedido = ?", (id_pedido,))
        cur.execute("DELETE FROM pedido WHERE id_pedido = ?", (id_pedido,))
        registrar_auditoria(conn, id_usuario, 'eliminar_factura', 'factura', id_factura,
                            f"Monto C${monto}", ip)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"status": "deleted", "id_factura": id_factura}


def _core_reporte_diario(conn, fecha):
    cur = conn.cursor()
    cur.execute("""SELECT COUNT(*), COALESCE(SUM(monto_total),0), COALESCE(SUM(impuesto),0),
                          COALESCE(SUM(propina),0), COALESCE(SUM(descuento),0)
                   FROM factura WHERE DATE(fecha_hora) = ?""", (fecha,))
    r = cur.fetchone()
    cur.execute("""SELECT metodo_pago, COUNT(*), COALESCE(SUM(monto_total),0)
                   FROM factura WHERE DATE(fecha_hora) = ? GROUP BY metodo_pago""", (fecha,))
    metodos = [{"metodo": m[0], "cantidad": m[1], "monto": float(m[2])} for m in cur.fetchall()]
    cur.execute("""SELECT dp.id_producto, pr.nombre, SUM(dp.cantidad), SUM(dp.subtotal)
                   FROM detalle_pedido dp
                   JOIN pedido p ON dp.id_pedido = p.id_pedido
                   JOIN factura f ON f.id_pedido = p.id_pedido
                   JOIN producto pr ON dp.id_producto = pr.id_producto
                   WHERE DATE(f.fecha_hora) = ?
                   GROUP BY dp.id_producto, pr.nombre
                   ORDER BY SUM(dp.cantidad) DESC LIMIT 10""", (fecha,))
    top = [{"id_producto": t[0], "nombre": t[1], "cantidad": t[2], "monto": float(t[3])} for t in cur.fetchall()]
    return {
        "fecha": fecha, "total_facturas": r[0],
        "total_ventas": float(r[1]), "total_impuesto": float(r[2]),
        "total_propinas": float(r[3]), "total_descuentos": float(r[4]),
        "por_metodo_pago": metodos, "top_productos": top,
    }


def _core_reporte_mensual(conn, anio, mes):
    pref = f"{int(anio):04d}-{int(mes):02d}"
    cur = conn.cursor()
    cur.execute("""SELECT COUNT(*), COALESCE(SUM(monto_total),0), COALESCE(SUM(impuesto),0)
                   FROM factura WHERE strftime('%Y-%m', fecha_hora) = ?""", (pref,))
    r = cur.fetchone()
    cur.execute("""SELECT DATE(fecha_hora) AS d, COUNT(*), COALESCE(SUM(monto_total),0)
                   FROM factura WHERE strftime('%Y-%m', fecha_hora) = ?
                   GROUP BY d ORDER BY d""", (pref,))
    por_dia = [{"fecha": x[0], "cantidad_facturas": x[1], "total": float(x[2])} for x in cur.fetchall()]
    cur.execute("""SELECT metodo_pago, COUNT(*), COALESCE(SUM(monto_total),0)
                   FROM factura WHERE strftime('%Y-%m', fecha_hora) = ?
                   GROUP BY metodo_pago""", (pref,))
    metodos = [{"metodo": m[0], "cantidad": m[1], "monto": float(m[2])} for m in cur.fetchall()]
    cur.execute("""SELECT dp.id_producto, pr.nombre, SUM(dp.cantidad), SUM(dp.subtotal)
                   FROM detalle_pedido dp
                   JOIN pedido p ON dp.id_pedido = p.id_pedido
                   JOIN factura f ON f.id_pedido = p.id_pedido
                   JOIN producto pr ON dp.id_producto = pr.id_producto
                   WHERE strftime('%Y-%m', f.fecha_hora) = ?
                   GROUP BY dp.id_producto, pr.nombre
                   ORDER BY SUM(dp.cantidad) DESC LIMIT 10""", (pref,))
    top = [{"id_producto": t[0], "nombre": t[1], "cantidad": t[2], "monto": float(t[3])} for t in cur.fetchall()]
    cur.execute("""SELECT c.nombre, SUM(dp.cantidad), SUM(dp.subtotal)
                   FROM detalle_pedido dp
                   JOIN pedido p ON dp.id_pedido = p.id_pedido
                   JOIN factura f ON f.id_pedido = p.id_pedido
                   JOIN producto pr ON dp.id_producto = pr.id_producto
                   JOIN categoria c ON pr.id_categoria = c.id_categoria
                   WHERE strftime('%Y-%m', f.fecha_hora) = ?
                   GROUP BY c.nombre ORDER BY SUM(dp.subtotal) DESC""", (pref,))
    cats = [{"categoria": x[0], "cantidad": x[1], "monto": float(x[2])} for x in cur.fetchall()]
    return {
        "anio": int(anio), "mes": int(mes),
        "total_facturas": r[0], "total_ventas": float(r[1]), "total_impuesto": float(r[2]),
        "por_dia": por_dia, "por_metodo_pago": metodos,
        "top_productos": top, "ventas_por_categoria": cats,
    }


def _validar_reserva(conn, data):
    nombre = (data.get('nombre_cliente') or '').strip()
    tel = (data.get('telefono') or '').strip()
    fecha = data.get('fecha_reserva') or ''
    hora = data.get('hora_reserva') or ''
    personas = int(data.get('num_personas') or 0)
    if len(nombre) < 3:   return "Nombre del cliente inválido"
    if len(tel) < 8:      return "Teléfono inválido"
    if not fecha:         return "Falta fecha"
    if fecha < date.today().isoformat():
        return "La fecha debe ser hoy o en adelante"
    if not (len(hora) == 5 and hora[2] == ':'):
        return "Hora inválida (HH:MM)"
    if not ('12:00' <= hora <= '22:00'):
        return "Hora fuera de rango (12:00-22:00)"
    if personas < 1 or personas > 30:
        return "Personas entre 1 y 30"
    id_mesa = data.get('id_mesa')
    if id_mesa:
        cur = conn.cursor()
        cur.execute("SELECT capacidad FROM mesa WHERE id_mesa = ?", (id_mesa,))
        m = cur.fetchone()
        if not m:
            return "Mesa no encontrada"
        if m['capacidad'] < personas:
            return "La mesa no tiene capacidad suficiente"
    return None


# ============================================================================
# BACKEND FLASK
# ============================================================================
try:
    from flask import Flask, jsonify, request, send_from_directory, g, redirect
    from flask_cors import CORS

    app = Flask(__name__, static_folder=BASE_DIR)
    CORS(app, supports_credentials=True,
         origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

    @app.before_request
    def _ensure_db():
        if 'db' not in g:
            g.db = get_db()

    @app.teardown_appcontext
    def _close_db(exc):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.after_request
    def _security_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        resp.headers['Referrer-Policy'] = 'same-origin'
        if request.path.startswith('/api/auth/'):
            resp.headers['Cache-Control'] = 'no-store'
        return resp

    PUBLIC_PATHS = {'/login.html', '/login.js', '/Login.css', '/MenuFilete.html',
                    '/menu.css', '/favicon.ico', '/api/auth/login', '/api/auth/register',
                    '/api/productos', '/api/categorias'}

    def _check_csrf():
        cookie = request.cookies.get('csrf_token', '')
        header = request.headers.get('X-CSRF-Token', '')
        return bool(cookie and header and hmac.compare_digest(cookie, header))

    @app.before_request
    def _check_auth():
        path = request.path
        if path in PUBLIC_PATHS or path.startswith('/Imagenes/'):
            return
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            if not _check_csrf():
                return jsonify({"error": "Token CSRF inválido o ausente"}), 403
        token = request.cookies.get('sesion_token')
        if not token:
            if path.startswith('/api/'):
                return jsonify({"error": "No autenticado"}), 401
            return redirect('/login.html')
        user = validar_sesion(g.db, token)
        if not user:
            if path.startswith('/api/'):
                return jsonify({"error": "Sesión inválida o expirada"}), 401
            return redirect('/login.html')
        g.usuario = user

    @app.route('/')
    def index():
        token = request.cookies.get('sesion_token')
        if token and validar_sesion(g.db, token):
            return redirect('/unificador.html')
        return redirect('/MenuFilete.html')

    @app.route('/<path:path>')
    def static_files(path):
        full = os.path.join(BASE_DIR, path)
        if os.path.exists(full):
            return send_from_directory(BASE_DIR, path)
        
        if path.endswith(('.js', '.css', '.jpg', '.png', '.webp')) or path.startswith('Imagenes/'):
            return "Archivo no encontrado", 404
            
        return redirect('/login.html')

    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        ip = request.remote_addr or ''
        ua = request.headers.get('User-Agent', '')

        if contar_intentos_fallidos(g.db, username, ip, 15) >= 5:
            return jsonify({"error": "Demasiados intentos. Espera 15 minutos."}), 429

        cur = g.db.cursor()
        cur.execute("SELECT id_usuario, password_hash, nombre_completo, rol, activo "
                    "FROM usuario WHERE username = ?", (username,))
        row = cur.fetchone()
        ok = bool(row) and row['activo'] and verify_password(password, row['password_hash'])

        if not ok:
            registrar_intento(g.db, username, ip, False)
            return jsonify({"error": "Credenciales inválidas"}), 401

        registrar_intento(g.db, username, ip, True)
        limpiar_sesiones_expiradas(g.db)
        token = crear_sesion(g.db, row['id_usuario'], ip, ua)
        csrf = generar_token()
        registrar_auditoria(g.db, row['id_usuario'], 'login',
                            entidad='usuario', entidad_id=row['id_usuario'], ip=ip)

        resp = jsonify({
            "id_usuario": row['id_usuario'], "username": username,
            "rol": row['rol'], "nombre_completo": row['nombre_completo'],
        })
        resp.set_cookie('sesion_token', token, max_age=8*3600, httponly=True,
                        samesite='Lax', secure=request.is_secure)
        resp.set_cookie('csrf_token', csrf, max_age=8*3600, httponly=False,
                        samesite='Lax', secure=request.is_secure)
        return resp, 200

    @app.route('/api/auth/register', methods=['POST'])
    def api_register():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        nombre = (data.get('nombre_completo') or '').strip() or username

        if len(username) < 3 or not all(c.isalnum() or c == '_' for c in username):
            return jsonify({"error": "Usuario inválido (mín. 3, alfanumérico/_)"}), 400
        if len(password) < 8:
            return jsonify({"error": "Contraseña de al menos 8 caracteres"}), 400

        cur = g.db.cursor()
        cur.execute("SELECT 1 FROM usuario WHERE username = ?", (username,))
        if cur.fetchone():
            return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

        try:
            cur.execute("""INSERT INTO usuario
                           (username, password_hash, nombre_completo, rol, activo)
                           VALUES (?, ?, ?, 'mesero', 1)""",
                        (username, hash_password(password), nombre))
            nuevo_id = cur.lastrowid
            registrar_auditoria(g.db, nuevo_id, 'registro_publico',
                                'usuario', nuevo_id, "Auto-registro web", request.remote_addr)
            g.db.commit()
        except sqlite3.IntegrityError as e:
            g.db.rollback()
            return jsonify({"error": str(e)}), 409

        return jsonify({"status": "success", "mensaje": "Usuario registrado correctamente. Ya puedes iniciar sesión."}), 201

    @app.route('/api/auth/logout', methods=['POST'])
    def api_logout():
        token = request.cookies.get('sesion_token')
        if token:
            invalidar_sesion(g.db, token)
            registrar_auditoria(g.db, g.usuario['id_usuario'], 'logout',
                                ip=request.remote_addr)
        resp = jsonify({"status": "ok"})
        resp.set_cookie('sesion_token', '', max_age=0)
        resp.set_cookie('csrf_token', '', max_age=0)
        return resp, 200

    @app.route('/api/auth/me', methods=['GET'])
    def api_me():
        u = g.usuario
        token = request.cookies.get('sesion_token')
        renovada = renovar_sesion_si_pronto_expira(g.db, token)
        resp = jsonify({
            "id_usuario": u['id_usuario'], "username": u['username'],
            "rol": u['rol'], "nombre_completo": u['nombre_completo'],
        })
        if renovada:
            resp.set_cookie('sesion_token', token, max_age=8*3600, httponly=True,
                            samesite='Lax', secure=request.is_secure)
        return resp, 200

    @app.route('/api/usuarios', methods=['GET'])
    def api_usuarios_list():
        if g.usuario['rol'] != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        cur = g.db.cursor()
        cur.execute("SELECT id_usuario, username, nombre_completo, rol, activo, fecha_creacion "
                    "FROM usuario ORDER BY id_usuario")
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    @app.route('/api/usuarios', methods=['POST'])
    def api_usuarios_create():
        creador = g.usuario
        if creador['rol'] not in ('admin', 'mesero'):
            return jsonify({"error": "Acceso denegado"}), 403
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        nombre = (data.get('nombre_completo') or '').strip() or username
        rol = data.get('rol') or 'mesero'

        if creador['rol'] == 'mesero' and rol != 'mesero':
            return jsonify({"error": "Un mesero solo puede crear meseros"}), 403
        if len(username) < 3 or not all(c.isalnum() or c == '_' for c in username):
            return jsonify({"error": "Username inválido"}), 400
        if len(password) < 8:
            return jsonify({"error": "Contraseña de al menos 8 caracteres"}), 400
        if rol not in ('admin', 'cajero', 'mesero'):
            return jsonify({"error": "Rol inválido"}), 400

        cur = g.db.cursor()
        cur.execute("SELECT 1 FROM usuario WHERE username = ?", (username,))
        if cur.fetchone():
            return jsonify({"error": "El username ya existe"}), 409
        if rol == 'admin':
            cur.execute("SELECT 1 FROM usuario WHERE rol='admin' AND activo=1")
            if cur.fetchone():
                return jsonify({"error": "Ya existe un administrador"}), 409

        try:
            cur.execute("""INSERT INTO usuario
                           (username, password_hash, nombre_completo, rol, activo, creado_por)
                           VALUES (?, ?, ?, ?, 1, ?)""",
                        (username, hash_password(password), nombre, rol, creador['id_usuario']))
            nuevo_id = cur.lastrowid
            registrar_auditoria(g.db, creador['id_usuario'], 'crear_usuario',
                                'usuario', nuevo_id, f"rol={rol}", request.remote_addr)
            g.db.commit()
        except sqlite3.IntegrityError as e:
            g.db.rollback()
            return jsonify({"error": str(e)}), 409
        return jsonify({"status": "created", "id_usuario": nuevo_id, "rol": rol}), 201

    @app.route('/api/usuarios/<int:uid>', methods=['DELETE'])
    def api_usuarios_delete(uid):
        if g.usuario['rol'] != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        if uid == g.usuario['id_usuario']:
            return jsonify({"error": "No puedes eliminarte a ti mismo"}), 409
        cur = g.db.cursor()
        cur.execute("SELECT * FROM usuario WHERE id_usuario = ?", (uid,))
        if not cur.fetchone():
            return jsonify({"error": "Usuario no encontrado"}), 404
        cur.execute("SELECT COUNT(*) FROM reserva WHERE creado_por = ?", (uid,))
        n_res = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM auditoria WHERE id_usuario = ?", (uid,))
        n_aud = cur.fetchone()[0]
        if n_res > 0 or n_aud > 0:
            g.db.execute("UPDATE usuario SET activo = 0 WHERE id_usuario = ?", (uid,))
            action = "desactivado (tenía historial)"
        else:
            g.db.execute("DELETE FROM usuario WHERE id_usuario = ?", (uid,))
            action = "eliminado"
        registrar_auditoria(g.db, g.usuario['id_usuario'], 'eliminar_usuario',
                            'usuario', uid, action, request.remote_addr)
        g.db.commit()
        return jsonify({"status": "ok", "accion": action}), 200

    @app.route('/api/facturas', methods=['GET'])
    def api_facturas_list():
        cur = g.db.cursor()
        cur.execute("""SELECT f.*, p.tipo_pedido, p.id_mesa, m.numero_mesa
                       FROM factura f
                       JOIN pedido p ON f.id_pedido = p.id_pedido
                       LEFT JOIN mesa m ON p.id_mesa = m.id_mesa
                       ORDER BY f.id_factura DESC""")
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    @app.route('/api/facturas/<int:id_factura>', methods=['GET'])
    def api_factura_detalle(id_factura):
        cur = g.db.cursor()
        cur.execute("""SELECT f.*, p.tipo_pedido, p.id_mesa, m.numero_mesa
                       FROM factura f
                       JOIN pedido p ON f.id_pedido = p.id_pedido
                       LEFT JOIN mesa m ON p.id_mesa = m.id_mesa
                       WHERE f.id_factura = ?""", (id_factura,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Factura no encontrada"}), 404
        f = dict(row)
        cur.execute("""SELECT dp.id_detalle, dp.id_producto, pr.nombre, dp.cantidad,
                              dp.precio_unitario, dp.subtotal, dp.observacion
                       FROM detalle_pedido dp
                       JOIN producto pr ON dp.id_producto = pr.id_producto
                       WHERE dp.id_pedido = ?
                       ORDER BY dp.id_detalle ASC""", (f['id_pedido'],))
        f['items'] = [dict(r) for r in cur.fetchall()]
        return jsonify(f), 200

    @app.route('/api/facturas/<int:id_factura>', methods=['DELETE'])
    def api_factura_delete(id_factura):
        if g.usuario['rol'] != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        if request.headers.get('X-Confirm-Delete', '').lower() != 'yes':
            return jsonify({"error": "Falta header X-Confirm-Delete: yes"}), 400
        try:
            return jsonify(_core_eliminar_factura(g.db, id_factura,
                                                  g.usuario['id_usuario'],
                                                  request.remote_addr)), 200
        except LookupError:
            return jsonify({"error": "Factura no encontrada"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/ventas', methods=['POST'])
    @app.route('/api/pedidos', methods=['POST'])
    def api_crear_venta():
        data = request.get_json(silent=True) or {}
        try:
            return jsonify(_core_crear_venta(g.db, data)), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/reservas', methods=['GET'])
    def api_reservas_list():
        cur = g.db.cursor()
        conds, vals = [], []
        if request.args.get('fecha'):
            conds.append("r.fecha_reserva = ?"); vals.append(request.args['fecha'])
        if request.args.get('estado'):
            conds.append("r.estado = ?"); vals.append(request.args['estado'])
        where = "WHERE " + " AND ".join(conds) if conds else ""
        cur.execute(f"""SELECT r.*, m.numero_mesa, u.username AS creador_username
                        FROM reserva r
                        LEFT JOIN mesa m ON r.id_mesa = m.id_mesa
                        LEFT JOIN usuario u ON r.creado_por = u.id_usuario
                        {where}
                        ORDER BY r.fecha_reserva ASC, r.hora_reserva ASC""", vals)
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    @app.route('/api/reservas', methods=['POST'])
    def api_reservas_create():
        data = request.get_json(silent=True) or {}
        err = _validar_reserva(g.db, data)
        if err:
            return jsonify({"error": err}), 400
        cur = g.db.cursor()
        cur.execute("""INSERT INTO reserva
                       (nombre_cliente, telefono, email, fecha_reserva, hora_reserva,
                        num_personas, id_mesa, notas, estado, creado_por)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)""",
                    (data['nombre_cliente'].strip(), data['telefono'].strip(),
                     (data.get('email') or '').strip() or None,
                     data['fecha_reserva'], data['hora_reserva'],
                     int(data['num_personas']), data.get('id_mesa') or None,
                     (data.get('notas') or '').strip() or None,
                     g.usuario['id_usuario']))
        rid = cur.lastrowid
        registrar_auditoria(g.db, g.usuario['id_usuario'], 'crear_reserva',
                            'reserva', rid, None, request.remote_addr)
        g.db.commit()
        return jsonify({"status": "created", "id_reserva": rid}), 201

    @app.route('/api/reservas/<int:rid>', methods=['PUT'])
    def api_reservas_update(rid):
        cur = g.db.cursor()
        cur.execute("SELECT * FROM reserva WHERE id_reserva = ?", (rid,))
        r = cur.fetchone()
        if not r:
            return jsonify({"error": "Reserva no encontrada"}), 404
        u = g.usuario
        if u['rol'] == 'mesero' and r['creado_por'] != u['id_usuario']:
            return jsonify({"error": "Acceso denegado"}), 403
        data = request.get_json(silent=True) or {}
        sets, vals = [], []
        for campo in ('nombre_cliente', 'telefono', 'email', 'fecha_reserva',
                      'hora_reserva', 'num_personas', 'id_mesa', 'notas'):
            if campo in data:
                sets.append(f"{campo} = ?"); vals.append(data[campo])
        if 'estado' in data:
            trans = {'pendiente': ('confirmada', 'cancelada'),
                     'confirmada': ('completada', 'cancelada'),
                     'completada': (), 'cancelada': ()}
            nuevo = data['estado']
            if nuevo != r['estado'] and nuevo not in trans.get(r['estado'], ()):
                return jsonify({"error": f"Transición {r['estado']} → {nuevo} no permitida"}), 400
            sets.append("estado = ?"); vals.append(nuevo)
        if not sets:
            return jsonify({"status": "noop"}), 200
        vals.append(rid)
        g.db.execute(f"UPDATE reserva SET {', '.join(sets)} WHERE id_reserva = ?", vals)
        registrar_auditoria(g.db, u['id_usuario'], 'editar_reserva',
                            'reserva', rid, None, request.remote_addr)
        g.db.commit()
        return jsonify({"status": "updated", "id_reserva": rid}), 200

    @app.route('/api/reservas/<int:rid>', methods=['DELETE'])
    def api_reservas_delete(rid):
        cur = g.db.cursor()
        cur.execute("SELECT creado_por FROM reserva WHERE id_reserva = ?", (rid,))
        r = cur.fetchone()
        if not r:
            return jsonify({"error": "Reserva no encontrada"}), 404
        u = g.usuario
        if u['rol'] != 'admin' and r['creado_por'] != u['id_usuario']:
            return jsonify({"error": "Acceso denegado"}), 403
        g.db.execute("DELETE FROM reserva WHERE id_reserva = ?", (rid,))
        registrar_auditoria(g.db, u['id_usuario'], 'eliminar_reserva',
                            'reserva', rid, None, request.remote_addr)
        g.db.commit()
        return jsonify({"status": "deleted", "id_reserva": rid}), 200

    @app.route('/api/reservas/disponibilidad', methods=['GET'])
    def api_reservas_disponibilidad():
        fecha = request.args.get('fecha')
        hora = request.args.get('hora')
        personas = int(request.args.get('personas') or 1)
        cur = g.db.cursor()
        if fecha and hora:
            cur.execute("""SELECT id_mesa, numero_mesa, capacidad FROM mesa
                           WHERE capacidad >= ?
                             AND id_mesa NOT IN (
                                SELECT id_mesa FROM reserva
                                WHERE fecha_reserva = ? AND hora_reserva = ?
                                  AND estado IN ('pendiente','confirmada')
                                  AND id_mesa IS NOT NULL)
                           ORDER BY numero_mesa""", (personas, fecha, hora))
        else:
            cur.execute("SELECT id_mesa, numero_mesa, capacidad FROM mesa "
                        "WHERE capacidad >= ? ORDER BY numero_mesa", (personas,))
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    @app.route('/api/categorias', methods=['GET'])
    def api_categorias():
        cur = g.db.cursor()
        cur.execute("SELECT id_categoria, nombre FROM categoria ORDER BY id_categoria")
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    @app.route('/api/productos', methods=['GET'])
    def api_productos():
        cur = g.db.cursor()
        cur.execute("""SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.imagen_url,
                              p.disponible, c.id_categoria, c.nombre AS categoria
                       FROM producto p
                       JOIN categoria c ON p.id_categoria = c.id_categoria
                       WHERE p.disponible = 1
                       ORDER BY c.id_categoria, p.id_producto""")
        data = [{"id_producto": r['id_producto'], "nombre": r['nombre'],
                 "descripcion": r['descripcion'] or "", "precio": float(r['precio']),
                 "imagen_url": r['imagen_url'] or "", "disponible": r['disponible'],
                 "id_categoria": r['id_categoria'], "categoria": r['categoria']}
                for r in cur.fetchall()]
        return jsonify(data), 200

    @app.route('/api/mesas', methods=['GET'])
    def api_mesas():
        cur = g.db.cursor()
        cur.execute("SELECT id_mesa, numero_mesa, capacidad, estado FROM mesa ORDER BY numero_mesa")
        return jsonify([dict(r) for r in cur.fetchall()]), 200

    def run_server(port=5000):
        print("=" * 65)
        print("   RESTAURANTE 'EL FILETE' - SERVIDOR BACKEND (FLASK + AUTH)")
        print("=" * 65)
        print(f" -> Base de datos : {DB_NAME}")
        print(f" -> http://localhost:{port}")
        print("=" * 65)
        app.run(host='0.0.0.0', port=port, debug=False)


except ImportError:
    print("Error: Flask no está instalado. Ejecuta: pip install flask flask-cors")

if __name__ == '__main__':
    run_server()