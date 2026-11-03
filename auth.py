import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "Filete2.db")

def get_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de datos no encontrada en {DB_PATH}. Ejecuta: python init_db.py")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

# --- AQUI ESTA LA FUNCION QUE FALTABA ---
def hash_password(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200000)
    return f"200000${salt.hex()}${dk.hex()}"

def verify_password(password, stored):
    try:
        partes = str(stored).split('$')
        if len(partes) != 3: return False
        iteraciones = int(partes[0])
        salt = bytes.fromhex(partes[1])
        esperado = bytes.fromhex(partes[2])
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iteraciones)
        return hmac.compare_digest(dk, esperado)
    except Exception:
        return False

def generar_token():
    return secrets.token_urlsafe(32)

def crear_sesion(conn, id_usuario, ip, user_agent, horas=8):
    token = generar_token()
    expira = (datetime.now(timezone.utc) + timedelta(hours=horas)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("INSERT INTO sesion (token, id_usuario, ip, user_agent, fecha_expiracion, activa) VALUES (?, ?, ?, ?, ?, 1)", (token, id_usuario, ip, user_agent, expira))
    conn.commit()
    return token

def validar_sesion(conn, token):
    if not token: return None
    cur = conn.cursor()
    cur.execute("""
        SELECT s.token, s.fecha_expiracion, u.id_usuario, u.username, u.rol, u.nombre_completo, u.activo
        FROM sesion s JOIN usuario u ON s.id_usuario = u.id_usuario
        WHERE s.token = ? AND s.activa = 1
    """, (token,))
    row = cur.fetchone()
    if not row or not row['activo']: return None
    expira = datetime.strptime(row['fecha_expiracion'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    if expira <= datetime.now(timezone.utc): return None
    return dict(row)

def renovar_sesion_si_pronto_expira(conn, token, umbral_min=60):
    cur = conn.cursor()
    cur.execute("SELECT fecha_expiracion FROM sesion WHERE token = ? AND activa = 1", (token,))
    row = cur.fetchone()
    if not row: return False
    expira = datetime.strptime(row['fecha_expiracion'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    if (expira - datetime.now(timezone.utc)) > timedelta(minutes=umbral_min): return False
    nueva = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("UPDATE sesion SET fecha_expiracion = ? WHERE token = ?", (nueva, token))
    conn.commit()
    return True

def invalidar_sesion(conn, token):
    conn.execute("UPDATE sesion SET activa = 0 WHERE token = ?", (token,))
    conn.commit()

def invalidar_sesiones_usuario(conn, id_usuario):
    conn.execute("UPDATE sesion SET activa = 0 WHERE id_usuario = ?", (id_usuario,))
    conn.commit()

def limpiar_sesiones_expiradas(conn):
    conn.execute("DELETE FROM sesion WHERE activa = 0 OR fecha_expiracion < datetime('now')")
    conn.commit()

def registrar_intento(conn, username, ip, exitoso):
    conn.execute("INSERT INTO intento_login (username, ip, exitoso) VALUES (?, ?, ?)", (username, ip, 1 if exitoso else 0))
    conn.commit()

def contar_intentos_fallidos(conn, username, ip, minutos=15):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM intento_login WHERE username = ? AND ip = ? AND exitoso = 0 AND fecha_hora > datetime('now', ?)", (username, ip, f'-{minutos} minutes'))
    return cur.fetchone()[0]

def registrar_auditoria(conn, id_usuario, accion, entidad=None, entidad_id=None, detalle=None, ip=None):
    conn.execute("INSERT INTO auditoria (id_usuario, accion, entidad, entidad_id, detalle, ip) VALUES (?, ?, ?, ?, ?, ?)", (id_usuario, accion, entidad, entidad_id, detalle, ip))
    conn.commit()