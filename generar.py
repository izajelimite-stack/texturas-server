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


# ---------------- Skylar ----------------
# La perrita de Fran (oct-2026), sacada de sus fotos: cuerpo negro rizado, pecho y guata blancos,
# patas blancas con pintas negras, barba blanca con nariz negra grande, cejas y mejillas color
# canela, orejas negras y cola negra con la punta blanca.
# Va encima del lobo de Fresh Animations (64x32, mismo lugar de cada parte que el lobo normal,
# mas sus ojos propios). Cada caja de Minecraft se despliega asi, con (u, v) la esquina y w, h, d
# el ancho, alto y fondo: arriba (u+d, v), abajo (u+d+w, v), lado (u, v+d), frente (u+d, v+d),
# otro lado (u+d+w, v+d), atras (u+2d+w, v+d). El cuerpo y el cuello van girados 90 grados: su
# "frente" es la guata y su "atras" el lomo.
NEGRO = [(26, 24, 28), (38, 35, 40), (18, 17, 20), (48, 44, 50)]
BLANCO = [(238, 236, 231), (224, 222, 216), (246, 245, 241), (210, 208, 203)]
CANELA = [(196, 150, 98), (178, 130, 80), (210, 168, 116)]
GRIS = [(196, 194, 190), (176, 174, 170)]


def skylar():
    import random
    azar = random.Random(7)  # siempre la misma textura
    pix = [[(0, 0, 0, 0)] * 64 for _ in range(32)]
    def pinta(x, y, paleta):
        pix[y][x] = azar.choice(paleta) + (255,)
    def caja(x0, y0, x1, y1, paleta):  # x1, y1 sin incluir
        for y in range(y0, y1):
            for x in range(x0, x1):
                pinta(x, y, paleta)
    def pintas(x0, y0, x1, y1, cuantas):  # puntitos negros sobre lo blanco
        for _ in range(cuantas):
            pinta(azar.randrange(x0, x1), azar.randrange(y0, y1), NEGRO[:3])

    # Cabeza: u0 v0, 6x6x4
    caja(4, 0, 10, 4, NEGRO)                       # arriba, rizos negros
    caja(10, 0, 16, 4, BLANCO)                     # abajo (debajo de la mandibula)
    caja(0, 4, 4, 10, NEGRO); caja(10, 4, 14, 10, NEGRO)   # lados
    caja(2, 7, 4, 10, BLANCO); caja(10, 7, 12, 10, BLANCO)  # barba que se ve de lado
    pinta(3, 7, CANELA); pinta(10, 7, CANELA)      # mejillas canela
    caja(4, 4, 10, 10, NEGRO)                      # cara
    for x in (5, 8):
        pinta(x, 5, CANELA)                        # cejas canela, sobre los ojos
    pinta(4, 5, CANELA); pinta(9, 5, CANELA)
    caja(4, 8, 10, 10, BLANCO)                     # barba bajo el hocico
    pinta(4, 7, CANELA); pinta(9, 7, CANELA)       # mejillas
    caja(14, 4, 20, 10, NEGRO)                     # nuca

    # Hocico: u1 v11, 3x3x3
    caja(4, 11, 7, 14, BLANCO)                     # arriba, blanco
    pinta(4, 11, GRIS); pinta(6, 11, GRIS)
    caja(7, 11, 10, 14, BLANCO)                    # abajo
    caja(1, 14, 13, 17, BLANCO)                    # lados, frente y atras
    pinta(3, 14, CANELA); pinta(7, 14, CANELA)     # canela atras de las mejillas
    pix[14][5] = (14, 13, 15, 255); pix[15][5] = (14, 13, 15, 255)  # nariz negra grande
    pix[14][4] = (40, 38, 42, 255); pix[14][6] = (40, 38, 42, 255)

    # Ojos de Fresh Animations: oscuros, como los de ella
    for (x, y) in ((11, 13), (12, 13), (15, 13), (16, 13), (12, 12), (15, 12)):
        pix[y][x] = (82, 54, 36, 255)
    pix[11][12] = (12, 10, 10, 255); pix[11][15] = (12, 10, 10, 255)

    # Orejas: u16 v14, 2x2x1, negras
    caja(16, 14, 22, 17, NEGRO)

    # Cuello (mane): u21 v0, 8x6x7
    caja(28, 0, 36, 7, NEGRO); caja(28, 3, 36, 7, BLANCO)  # frente: arriba negro, pecho blanco
    caja(36, 0, 44, 7, NEGRO)                      # hacia el cuerpo
    caja(21, 7, 28, 13, NEGRO); caja(25, 7, 28, 13, BLANCO)  # lado: abajo blanco
    caja(36, 7, 43, 13, NEGRO); caja(36, 7, 39, 13, BLANCO)  # otro lado
    caja(28, 7, 36, 13, BLANCO)                    # bajo el cuello: pecho blanco
    caja(43, 7, 51, 13, NEGRO)                     # lomo del cuello

    # Cuerpo: u18 v14, 6x9x6
    caja(24, 14, 30, 20, NEGRO); caja(24, 17, 30, 20, BLANCO)  # parte de adelante: pecho blanco abajo
    caja(30, 14, 36, 20, NEGRO)                    # parte de atras (anca)
    caja(18, 20, 24, 29, NEGRO); caja(36, 20, 42, 29, NEGRO)   # un lado y el lomo
    caja(30, 20, 36, 29, NEGRO)                    # otro lado
    caja(21, 20, 24, 24, BLANCO); pintas(21, 20, 24, 24, 3)    # mancha blanca con pintas, adelante
    caja(30, 20, 33, 24, BLANCO); pintas(30, 20, 33, 24, 3)
    caja(24, 20, 30, 29, BLANCO); pintas(24, 25, 30, 29, 4)    # guata blanca

    # Patas: u0 v18, 2x8x2, blancas con pintas, arriba negras
    caja(2, 18, 4, 20, NEGRO); caja(4, 18, 6, 20, BLANCO)
    caja(0, 20, 8, 28, BLANCO)
    caja(0, 20, 8, 21, NEGRO)
    pintas(0, 21, 8, 26, 6)

    # Cola: u9 v18, 2x8x2, negra con la punta blanca
    caja(11, 18, 13, 20, NEGRO); caja(13, 18, 15, 20, BLANCO)
    caja(9, 20, 17, 28, NEGRO); caja(9, 25, 17, 28, BLANCO)
    return png(64, 32, pix)


# Las 9 razas de lobo de 26.x, cada una con su textura normal, mansa y enojada. Un lobo llamado
# Skylar usa la de ella en cualquiera (Entity Texture Features, del modpack).
LOBOS = ["wolf", "wolf_ashen", "wolf_black", "wolf_chestnut", "wolf_rusty", "wolf_snowy",
         "wolf_spotted", "wolf_striped", "wolf_woods"]


def secretos_por_nombre(pack):
    carpeta = os.path.join(pack, "assets", "minecraft", "optifine", "random", "entity", "wolf")
    os.makedirs(carpeta, exist_ok=True)
    textura = skylar()
    for raza in LOBOS:
        for estado in ("", "_tame", "_angry"):
            nombre = raza + estado
            open(os.path.join(carpeta, nombre + "2.png"), "wb").write(textura)
            with open(os.path.join(carpeta, nombre + ".properties"), "w", encoding="utf-8") as f:
                f.write("# Secreto: un lobo con la etiqueta Skylar se ve como la perrita de Fran.\n"
                        "textures.2=2\nname.2=ipattern:Skylar\n")


def armar(version):
    base = os.path.dirname(os.path.abspath(__file__))
    pack = os.path.join(base, "pack")
    secretos_por_nombre(pack)
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
