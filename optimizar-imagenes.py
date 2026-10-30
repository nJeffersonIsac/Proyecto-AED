from PIL import Image
import os

CARPETA_ORIGEN = "imagenes"
CARPETA_DESTINO = "imagenes_opt"
MAX_ANCHO = 1200        # px. Suficiente para verse bien en pantalla
CALIDAD = 75            # 70-80 es buen balance calidad/peso
PESO_OBJETIVO_KB = 120  # Si supera esto, baja más la calidad

os.makedirs(CARPETA_DESTINO, exist_ok=True)

total_antes = 0
total_despues = 0

for nombre in os.listdir(CARPETA_ORIGEN):
    if not nombre.lower().endswith((".jpg", ".jpeg")):
        continue

    ruta_in = os.path.join(CARPETA_ORIGEN, nombre)
    ruta_out = os.path.join(CARPETA_DESTINO, nombre)

    peso_antes = os.path.getsize(ruta_in)
    total_antes += peso_antes

    img = Image.open(ruta_in).convert("RGB")

    # Redimensionar si es más ancha que MAX_ANCHO
    if img.width > MAX_ANCHO:
        ratio = MAX_ANCHO / img.width
        nuevo_alto = int(img.height * ratio)
        img = img.resize((MAX_ANCHO, nuevo_alto), Image.LANCZOS)

    # Guardar con calidad ajustada, bajando si aún pesa mucho
    calidad = CALIDAD
    while True:
        img.save(ruta_out, "JPEG", quality=calidad, optimize=True, progressive=True)
        peso_despues = os.path.getsize(ruta_out)
        if peso_despues <= PESO_OBJETIVO_KB * 1024 or calidad <= 40:
            break
        calidad -= 5

    total_despues += peso_despues
    print(f"{nombre}: {peso_antes//1024} KB -> {peso_despues//1024} KB (calidad {calidad})")

print("\n--- RESUMEN ---")
print(f"Antes : {total_antes/1024/1024:.2f} MB")
print(f"Después: {total_despues/1024/1024:.2f} MB")
print(f"Ahorro : {100 - (total_despues/total_antes*100):.1f}%")