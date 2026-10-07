"""Arma el paquete de texturas del server desde cero (PNG a mano, sin librerias).

Trae:
 - los fondos de los menus propios (plugin Viajes): se dibujan como una "letra" gigante en el
   titulo del menu (fuente amigos:menus), con hoyos donde van las casillas. Sin mods.
 - Skylar, la perrita de Fran: un lobo con la etiqueta "Skylar" se ve como ella, con su propio
   modelo (orejas largas colgando, copete, barba). Usa Entity Texture Features y Entity Model
   Features, que vienen en Fabulously Optimized. El modelo parte del lobo de Fresh Animations
   (de FreshLX, https://modrinth.com/resourcepack/fresh-animations), modificado, con credito.

Uso: python3 generar.py <version>   ->  dist/texturas-v<version>.zip
"""
import json, os, struct, sys, zlib, zipfile, hashlib, random, urllib.request, io, copy

ANCHO = 176
BASE = os.path.dirname(os.path.abspath(__file__))


def png(ancho, alto, pix):
    crudo = b"".join(b"\x00" + bytes(c for p in pix[y] for c in p) for y in range(alto))
    def trozo(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(crudo, 9)) + trozo(b"IEND", b""))


# ---------------- menus ----------------

TEMAS = {
    # Teletransporte: turquesa suave, como una perla de ender, con detalles dorados.
    "viajes": dict(borde=(28, 34, 40), luz=(232, 248, 246), relleno=(190, 218, 214), banda=(172, 205, 200),
                   sombra=(88, 124, 120), casilla_osc=(52, 66, 68), casilla_clara=(244, 252, 251), oro=(201, 158, 46)),
    # Mis permisos: pergamino tibio con detalles dorados.
    "permisos": dict(borde=(44, 32, 22), luz=(255, 249, 234), relleno=(228, 214, 182), banda=(214, 196, 158),
                     sombra=(138, 110, 72), casilla_osc=(88, 68, 44), casilla_clara=(255, 251, 238), oro=(176, 126, 36)),
}
FILAS = range(2, 7)  # los menus usan de 2 a 6 filas


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
# Sacada de 16 fotos (oct-2026): cockapoo negra de pelo rizado. Cabeza negra con cejas rubias
# (solo las cejas), ojos cafe oscuro, barba y hocico blancos, nariz negra grande, orejas largas
# negras y rizadas que cuelgan. Pecho y guata blancos; una mancha blanca con pintas negras detras
# del cuello, en el lomo y los costados. Patas blancas con pintas, muslos negros. Cola negra con
# la punta blanca.
#
# Va sobre la distribucion del lobo de Fresh Animations (64x32). Cada caja se despliega asi, con
# (u, v) la esquina y w, h, d ancho, alto y fondo: arriba (u+d, v), abajo (u+d+w, v), lado
# (u, v+d), frente (u+d, v+d), otro lado (u+d+w, v+d), atras (u+2d+w, v+d). En el cuerpo y el
# cuello (girados 90 grados) el "frente" es la guata y el "atras" el lomo.
# La cara (6x6): fila 1 = cejas, filas 2 y 3 = ojos (en las 2 columnas de cada orilla), filas 4 a 6
# = hocico al medio y mejillas a los lados.
NEGRO = [(22, 21, 24), (30, 28, 32), (38, 36, 41), (46, 43, 48), (58, 52, 54)]
BLANCO = [(242, 239, 231), (233, 229, 219), (248, 246, 240), (224, 219, 207)]
CREMA = [(232, 224, 205), (222, 212, 190)]
RUBIO = [(226, 188, 132), (212, 170, 112), (232, 198, 146)]
GRIS = [(150, 146, 140), (120, 116, 112)]
OJO = (92, 60, 40)
PUPILA = (10, 9, 10)
OREJA = [(36, 31, 30), (48, 41, 38), (28, 25, 26), (60, 50, 44)]
NARIZ = (14, 13, 15)

# Partes nuevas del modelo de Skylar y donde va su textura (en lugares libres de la imagen).
OREJA_UV = (44, 14)    # caja 1x5x3
COPETE_UV = (44, 23)   # caja 4x1x3


def skylar():
    azar = random.Random(7)  # siempre la misma textura
    pix = [[(0, 0, 0, 0)] * 64 for _ in range(32)]
    def pinta(x, y, paleta):
        pix[y][x] = azar.choice(paleta) + (255,)
    def fijo(x, y, c):
        pix[y][x] = c + (255,)
    def caja(x0, y0, x1, y1, paleta):  # x1, y1 sin incluir
        for y in range(y0, y1):
            for x in range(x0, x1):
                pinta(x, y, paleta)
    def pintas(x0, y0, x1, y1, cuantas):  # puntitos negros sobre lo blanco
        for _ in range(cuantas):
            pinta(azar.randrange(x0, x1), azar.randrange(y0, y1), NEGRO[:2])
    def desplegar(u, v, w, h, d):
        """Las 6 caras de una caja: arriba, abajo, lado1, frente, lado2, atras (x0, y0, x1, y1)."""
        return dict(arriba=(u + d, v, u + d + w, v + d), abajo=(u + d + w, v, u + d + 2 * w, v + d),
                    lado1=(u, v + d, u + d, v + d + h), frente=(u + d, v + d, u + d + w, v + d + h),
                    lado2=(u + d + w, v + d, u + 2 * d + w, v + d + h), atras=(u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h))

    # Cabeza: u0 v0, 6x6x4
    c = desplegar(0, 0, 6, 6, 4)
    caja(*c["arriba"], NEGRO); caja(*c["atras"], NEGRO)
    caja(*c["lado1"], NEGRO); caja(*c["lado2"], NEGRO)
    caja(*c["abajo"], BLANCO)                      # bajo la mandibula
    x0, y0 = c["frente"][:2]                       # cara, 6x6 desde (4, 4)
    caja(x0, y0, x0 + 6, y0 + 6, NEGRO)
    for x in (0, 1, 4, 5):
        pinta(x0 + x, y0, RUBIO)                   # cejas rubias, sobre cada ojo
    # Fila 4 (bajo los ojos): aqui empieza el blanco del hocico, con negro en las orillas.
    for x in range(6):
        pinta(x0 + x, y0 + 3, NEGRO if x in (0, 5) else BLANCO)
    # Filas 5 y 6 a los lados del hocico: barba blanca, gris en la orilla.
    for y in (4, 5):
        for x in (0, 1, 4, 5):
            pinta(x0 + x, y0 + y, GRIS if x in (0, 5) else BLANCO)
    # Ojos de Fresh Animations: chicos y oscuros, como los de ella (sin brillo: un pixel entero
    # de brillo los hacia ver grandes). El pixel de arriba del ojo queda del color del pelo.
    for (x, y) in ((11, 13), (12, 13), (15, 13), (16, 13)):
        fijo(x, y, OJO)
    fijo(12, 12, NEGRO[1]); fijo(15, 12, NEGRO[1])
    fijo(12, 11, PUPILA); fijo(15, 11, PUPILA)

    # Hocico corto (el de ella es chato): u1 v11, 3x2x2. Blanco, con la nariz negra ancha arriba
    # (asi queda separada de la frente por la fila blanca de la cara).
    c = desplegar(1, 11, 3, 2, 2)
    for k in ("arriba", "abajo", "lado1", "lado2", "atras", "frente"):
        caja(*c[k], BLANCO)
    ax, ay = c["arriba"][:2]                       # arriba: la fila de abajo es la punta
    fijo(ax + 1, ay + 1, NARIZ)
    fx, fy = c["frente"][:2]
    fijo(fx, fy, (64, 58, 60)); fijo(fx + 1, fy, NARIZ); fijo(fx + 2, fy, (64, 58, 60))  # nariz redonda
    pinta(fx, fy + 1, BLANCO); fijo(fx + 1, fy + 1, (110, 102, 100)); pinta(fx + 2, fy + 1, BLANCO)  # boca

    # Orejas largas que cuelgan (partes nuevas del modelo): 1x5x3, negras y rizadas, con el brillo
    # tibio que tienen los rizos en las fotos (asi se distinguen de la cabeza).
    c = desplegar(*OREJA_UV, 1, 5, 3)
    for k in c:
        caja(*c[k], OREJA)
    # Copete rizado sobre la cabeza: 4x1x3
    c = desplegar(*COPETE_UV, 4, 1, 3)
    for k in c:
        caja(*c[k], NEGRO)

    # Cuello (mane): u21 v0, 8x6x7
    c = desplegar(21, 0, 8, 6, 7)
    caja(*c["arriba"], NEGRO); caja(28, 3, 36, 7, BLANCO)   # frente del pecho: blanco abajo
    caja(*c["abajo"], NEGRO)
    caja(*c["lado1"], NEGRO); caja(25, 7, 28, 13, BLANCO)   # costados: abajo blanco
    caja(*c["lado2"], NEGRO); caja(36, 7, 39, 13, BLANCO)
    caja(*c["frente"], BLANCO)                     # bajo el cuello
    caja(*c["atras"], NEGRO)                       # nuca y cruz
    caja(43, 11, 51, 13, BLANCO); pintas(43, 11, 51, 13, 4)  # empieza la mancha detras del cuello

    # Cuerpo: u18 v14, 6x9x6 (v20 = adelante, v28 = atras)
    c = desplegar(18, 14, 6, 9, 6)
    caja(*c["arriba"], BLANCO); caja(24, 14, 30, 16, NEGRO)  # pecho blanco, arriba negro
    caja(*c["abajo"], NEGRO)                       # anca
    caja(*c["lado1"], NEGRO); caja(*c["lado2"], NEGRO)
    caja(*c["frente"], BLANCO); pintas(24, 25, 30, 29, 3)    # guata blanca
    caja(*c["atras"], NEGRO)                       # lomo
    caja(36, 20, 42, 23, BLANCO); pintas(36, 20, 42, 23, 6)  # mancha blanca con pintas en el lomo
    caja(18, 20, 21, 23, BLANCO); pintas(18, 20, 21, 23, 3)  # y en los costados, junto al lomo
    caja(33, 20, 36, 23, BLANCO); pintas(33, 20, 36, 23, 3)
    caja(22, 20, 24, 24, BLANCO); caja(30, 20, 32, 24, BLANCO)  # pecho que se ve de lado

    # Patas: u0 v18, 2x8x2. Arriba negras (muslos), abajo blancas con pintas.
    c = desplegar(0, 18, 2, 8, 2)
    caja(*c["arriba"], NEGRO); caja(*c["abajo"], CREMA)
    caja(0, 20, 8, 28, BLANCO)
    caja(0, 20, 8, 22, NEGRO)
    pintas(0, 22, 8, 26, 7)

    # Cola: u9 v18, 2x8x2 (v20 = base, v27 = punta). Negra con la punta blanca.
    c = desplegar(9, 18, 2, 8, 2)
    caja(*c["arriba"], NEGRO); caja(*c["abajo"], BLANCO)
    caja(9, 20, 17, 28, NEGRO); caja(9, 25, 17, 28, BLANCO)
    return png(64, 32, pix)


# El lobo de Fresh Animations, para hacer la version de Skylar.
FA_URL = "https://cdn.modrinth.com/data/50dA9Sha/versions/RGIzA5em/FreshAnimations_v1.10.5.zip"


def lobo_fresh_animations():
    cache = os.path.join(BASE, ".cache", "FreshAnimations_v1.10.5.zip")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        datos = urllib.request.urlopen(urllib.request.Request(FA_URL, headers={"User-Agent": "texturas-server"}), timeout=60).read()
        open(cache, "wb").write(datos)
    return json.loads(zipfile.ZipFile(cache).read("assets/minecraft/optifine/cem/wolf.jem"))


def modelo_skylar():
    """El lobo de Fresh Animations con orejas largas que cuelgan, copete y hocico corto.

    Las orejas de Fresh Animations se dejan sin caja (sus animaciones siguen ahi y no fallan) y se
    agregan otras, quietas, a los lados de la cabeza. Coordenadas en el formato de OptiFine
    (invertAxis xy): la cabeza va de x -3 a 3, de y -3.5 a 2.5 y de z -4.5 a -0.5.
    """
    jem = copy.deepcopy(lobo_fresh_animations())
    def buscar(p, nombre):
        for s in p.get("submodels", []):
            if s.get("id") == nombre:
                return s
            r = buscar(s, nombre)
            if r:
                return r
        return None
    cuerpo = next(m for m in jem["models"] if m.get("part") == "body")
    cabeza = buscar(cuerpo, "head2")
    hocico = buscar(cabeza, "snout")
    for oreja in ("left_ear", "right_ear"):
        buscar(cabeza, oreja)["boxes"] = []
    def parte(nombre, tr, coords, uv, espejo=False):
        p = {"id": nombre, "invertAxis": "xy", "translate": tr,
             "boxes": [{"coordinates": coords, "textureOffset": list(uv)}]}
        if espejo:
            p["mirrorTexture"] = "u"
        return p
    # Orejas: desde arriba de la cabeza, por fuera de los costados, 5 de largo.
    cabeza["submodels"].append(parte("oreja_skylar_i", [-3.5, 2, -2], [-0.5, -5, -1.5, 1, 5, 3], OREJA_UV, True))
    cabeza["submodels"].append(parte("oreja_skylar_d", [3.5, 2, -2], [-0.5, -5, -1.5, 1, 5, 3], OREJA_UV))
    # Copete rizado arriba de la cabeza, hacia adelante.
    cabeza["submodels"].append(parte("copete_skylar", [0, 2.5, -3], [-2, 0, -1.5, 4, 1, 3], COPETE_UV))
    # Hocico corto y chato (el de Fresh Animations es 3x3x3 y en ella se veia como un bloque grande):
    # 3 de ancho, 2 de alto y 2 de largo, abajo en la cara. Mismo nombre, asi lo siguen animando.
    hocico["boxes"] = [{"coordinates": [-1.5, 0, -2, 3, 2, 2], "textureOffset": [1, 11]}]
    jem["credit"] = "Lobo de Fresh Animations por FreshLX (modrinth.com/resourcepack/fresh-animations), modificado para Skylar"
    return jem


# Las 9 razas de lobo de 26.x, cada una con su textura normal, mansa y enojada. Un lobo llamado
# Skylar usa la de ella en cualquiera (Entity Texture Features, del modpack).
LOBOS = ["wolf", "wolf_ashen", "wolf_black", "wolf_chestnut", "wolf_rusty", "wolf_snowy",
         "wolf_spotted", "wolf_striped", "wolf_woods"]
REGLA = "# Secreto: un lobo con la etiqueta Skylar se ve como la perrita de Fran.\n"


def secretos_por_nombre(pack):
    carpeta = os.path.join(pack, "assets", "minecraft", "optifine", "random", "entity", "wolf")
    os.makedirs(carpeta, exist_ok=True)
    textura = skylar()
    for raza in LOBOS:
        for estado in ("", "_tame", "_angry"):
            nombre = raza + estado
            open(os.path.join(carpeta, nombre + "2.png"), "wb").write(textura)
            with open(os.path.join(carpeta, nombre + ".properties"), "w", encoding="utf-8") as f:
                f.write(REGLA + "textures.2=2\nname.2=ipattern:Skylar\n")
    cem = os.path.join(pack, "assets", "minecraft", "optifine", "cem")
    os.makedirs(cem, exist_ok=True)
    json.dump(modelo_skylar(), open(os.path.join(cem, "wolf2.jem"), "w", encoding="utf-8"), indent=1)
    with open(os.path.join(cem, "wolf.properties"), "w", encoding="utf-8") as f:
        f.write(REGLA + "models.2=2\nname.2=ipattern:Skylar\n")
    return textura


def armar(version):
    pack = os.path.join(BASE, "pack")
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
    json.dump({"pack": {"description": "Server de los amigos: menus y Skylar (lobo basado en Fresh Animations de FreshLX)",
                        "min_format": 84, "max_format": 999}},
              open(os.path.join(pack, "pack.mcmeta"), "w", encoding="utf-8"), indent=2)
    os.makedirs(os.path.join(BASE, "dist"), exist_ok=True)
    salida = os.path.join(BASE, "dist", f"texturas-v{version}.zip")
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
