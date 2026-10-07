"""Arma el paquete de texturas del server desde cero (sin librerias: PNG a mano).

Por ahora trae los fondos de los menus propios (plugin Viajes): se dibujan como una "letra"
gigante en el titulo del menu (fuente amigos:menus), con hoyos transparentes donde van las
casillas para que los objetos se vean. Funciona en Minecraft normal, sin mods.

Uso: python3 generar.py <version>   ->  dist/texturas-v<version>.zip
"""
import json, os, struct, sys, zlib, zipfile, hashlib

ANCHO = 176

TEMAS = {
    # Teletransporte: turquesa suave, como una perla de ender, con detalles dorados.
    "viajes": dict(borde=(28, 34, 40), luz=(232, 248, 246), relleno=(190, 218, 214), banda=(172, 205, 200),
                   sombra=(88, 124, 120), casilla_osc=(52, 66, 68), casilla_clara=(244, 252, 251), oro=(201, 158, 46)),
    # Mis permisos: pergamino tibio con detalles dorados.
    "permisos": dict(borde=(44, 32, 22), luz=(255, 249, 234), relleno=(228, 214, 182), banda=(214, 196, 158),
                     sombra=(138, 110, 72), casilla_osc=(88, 68, 44), casilla_clara=(255, 251, 238), oro=(176, 126, 36)),
}
FILAS = range(2, 7)  # los menus usan de 2 a 6 filas


def png(ancho, alto, pix):
    crudo = b"".join(b"\x00" + bytes(c for p in pix[y] for c in p) for y in range(alto))
    def trozo(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(crudo, 9)) + trozo(b"IEND", b""))


def fondo(tema, filas):
    t = TEMAS[tema]
    alto = 114 + filas * 18
    vacio = (0, 0, 0, 0)
    pix = [[vacio] * ANCHO for _ in range(alto)]
    def p(x, y, c):
        if 0 <= x < ANCHO and 0 <= y < alto:
            pix[y][x] = c + (255,) if len(c) == 3 else c
    def caja(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                p(x, y, c)
    a, h = ANCHO - 1, alto - 1
    # Panel con esquinas redondeadas como el de Minecraft: borde, luz arriba-izquierda, sombra abajo-derecha.
    caja(3, 3, a - 3, h - 3, t["relleno"])
    caja(2, 0, a - 2, 0, t["borde"]); caja(2, h, a - 2, h, t["borde"])
    caja(0, 2, 0, h - 2, t["borde"]); caja(a, 2, a, h - 2, t["borde"])
    for x, y in ((1, 1), (a - 1, 1), (1, h - 1), (a - 1, h - 1)):
        p(x, y, t["borde"])
    caja(2, 1, a - 2, 2, t["luz"]); caja(1, 2, 2, h - 3, t["luz"])
    caja(3, h - 2, a - 1, h - 1, t["sombra"]); caja(a - 2, 3, a - 1, h - 2, t["sombra"])
    p(a - 1, 1, t["borde"]); p(1, h - 1, t["borde"])
    # Franja del titulo y una linea dorada bajo ella.
    caja(4, 4, a - 4, 14, t["banda"])
    caja(7, 15, a - 7, 15, t["oro"])
    # Adornos dorados en las esquinas de adentro.
    for (x, y, dx, dy) in ((4, 4, 1, 1), (a - 4, 4, -1, 1), (4, h - 4, 1, -1), (a - 4, h - 4, -1, -1)):
        p(x, y, t["oro"]); p(x + dx, y, t["oro"]); p(x, y + dy, t["oro"])
    # Linea dorada sobre "Inventario".
    y0 = 17 + filas * 18
    caja(7, y0 + 1, a - 7, y0 + 1, t["oro"])

    def casilla(fx, fy):
        caja(fx, fy, fx + 16, fy, t["casilla_osc"]); caja(fx, fy, fx, fy + 16, t["casilla_osc"])
        caja(fx + 1, fy + 17, fx + 17, fy + 17, t["casilla_clara"]); caja(fx + 17, fy + 1, fx + 17, fy + 17, t["casilla_clara"])
        p(fx + 17, fy, t["relleno"]); p(fx, fy + 17, t["relleno"])
        caja(fx + 1, fy + 1, fx + 16, fy + 16, vacio)  # hoyo: ahi se ve el objeto
    for f in range(filas):
        for c in range(9):
            casilla(7 + 18 * c, 17 + 18 * f)
    for f in range(3):
        for c in range(9):
            casilla(7 + 18 * c, y0 + 13 + 18 * f)
    for c in range(9):
        casilla(7 + 18 * c, y0 + 71)
    return png(ANCHO, alto, pix)


def armar(version):
    base = os.path.dirname(os.path.abspath(__file__))
    pack = os.path.join(base, "pack")
    proveedores = [{"type": "space", "advances": {"": -1, "": -8, "": -32, "": -128}}]
    for tema, inicio in (("viajes", 0xE100), ("permisos", 0xE200)):
        for filas in FILAS:
            nombre = f"{tema}_{filas}.png"
            ruta = os.path.join(pack, "assets", "amigos", "textures", "font", "menus", nombre)
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            open(ruta, "wb").write(fondo(tema, filas))
            # ascent 13: el titulo se dibuja en y=6, y asi la imagen parte en y=0 del menu.
            proveedores.append({"type": "bitmap", "file": f"amigos:font/menus/{nombre}",
                                "ascent": 13, "height": 114 + filas * 18, "chars": [chr(inicio + filas)]})
    fuente = os.path.join(pack, "assets", "amigos", "font", "menus.json")
    os.makedirs(os.path.dirname(fuente), exist_ok=True)
    json.dump({"providers": proveedores}, open(fuente, "w", encoding="utf-8"), ensure_ascii=True, indent=2)
    json.dump({"pack": {"description": "Server de los amigos: menus y detalles", "min_format": 84, "max_format": 999}},
              open(os.path.join(pack, "pack.mcmeta"), "w", encoding="utf-8"), indent=2)
    os.makedirs(os.path.join(base, "dist"), exist_ok=True)
    salida = os.path.join(base, "dist", f"texturas-v{version}.zip")
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, archivos in os.walk(pack):
            for a in sorted(archivos):
                completo = os.path.join(raiz, a)
                info = zipfile.ZipInfo(os.path.relpath(completo, pack).replace(os.sep, "/"), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, open(completo, "rb").read())
    sha1 = hashlib.sha1(open(salida, "rb").read()).hexdigest()
    print(f"{salida} {os.path.getsize(salida)} bytes sha1 {sha1}")


if __name__ == "__main__":
    armar(sys.argv[1] if len(sys.argv) > 1 else "1")
