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

    # Hocico: u1 v11, 3x3x2 (alto como el de ella, pero corto hacia adelante). Blanco: arriba el
    # puente blanco, al medio la nariz negra redonda, abajo la boca. Asi la nariz queda sobre blanco
    # y no se junta con la frente negra.
    c = desplegar(1, 11, 3, 3, 2)
    for k in ("arriba", "abajo", "lado1", "lado2", "atras", "frente"):
        caja(*c[k], BLANCO)
    fx, fy = c["frente"][:2]
    fijo(fx, fy + 1, (64, 58, 60)); fijo(fx + 1, fy + 1, NARIZ); fijo(fx + 2, fy + 1, (64, 58, 60))  # nariz redonda
    fijo(fx + 1, fy + 2, (110, 102, 100))          # boca
    fijo(c["lado1"][2] - 1, c["lado1"][1] + 1, (64, 58, 60))  # costados de la nariz
    fijo(c["lado2"][0], c["lado2"][1] + 1, (64, 58, 60))

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
    # Hocico corto (el de Fresh Animations es 3x3x3 y en ella se veia como un bloque largo): 3 de
    # ancho y 3 de alto como el de ella, pero solo 2 de largo. Mismo nombre, asi lo siguen animando.
    # (Con 2 de alto, Fran lo encontro muy bajo y raro.)
    hocico["boxes"] = [{"coordinates": [-1.5, 0, -2, 3, 3, 2], "textureOffset": [1, 11]}]
    jem["credit"] = "Lobo de Fresh Animations por FreshLX (modrinth.com/resourcepack/fresh-animations), modificado para Skylar"
    return jem


def leer_png(d):
    """PNG -> (ancho, alto, filas de (r, g, b, a)). Alcanza para las texturas de Minecraft."""
    w, h = struct.unpack(">II", d[16:24]); prof, tipo = d[24], d[25]
    pos, idat, plte, trns = 8, b"", b"", b""
    while pos < len(d):
        n = struct.unpack(">I", d[pos:pos + 4])[0]; t = d[pos + 4:pos + 8]; c = d[pos + 8:pos + 8 + n]
        if t == b"IDAT": idat += c
        elif t == b"PLTE": plte = c
        elif t == b"tRNS": trns = c
        pos += 12 + n
    assert prof == 8, "solo PNG de 8 bits"
    bpp = {6: 4, 2: 3, 3: 1, 4: 2, 0: 1}[tipo]
    raw = zlib.decompress(idat); filas = []; prev = bytearray(w * bpp); i = 0
    for _ in range(h):
        f = raw[i]; i += 1; lin = bytearray(raw[i:i + w * bpp]); i += w * bpp
        for x in range(len(lin)):
            a = lin[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: lin[x] = (lin[x] + a) & 255
            elif f == 2: lin[x] = (lin[x] + b) & 255
            elif f == 3: lin[x] = (lin[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                lin[x] = (lin[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        filas.append(lin); prev = lin
    pix = []
    for fila in filas:
        if tipo == 6: pix.append([tuple(fila[x * 4:x * 4 + 4]) for x in range(w)])
        elif tipo == 2: pix.append([tuple(fila[x * 3:x * 3 + 3]) + (255,) for x in range(w)])
        elif tipo == 3: pix.append([tuple(plte[k * 3:k * 3 + 3]) + ((trns[k] if k < len(trns) else 255),) for k in fila])
        elif tipo == 4: pix.append([(fila[x * 2],) * 3 + (fila[x * 2 + 1],) for x in range(w)])
        else: pix.append([(v, v, v, 255) for v in fila])
    return w, h, pix


def textura_fa(ruta):
    lobo_fresh_animations()  # deja bajado el zip de Fresh Animations en .cache
    z = zipfile.ZipFile(os.path.join(BASE, ".cache", "FreshAnimations_v1.10.5.zip"))
    return leer_png(z.read("assets/minecraft/textures/entity/" + ruta))


def teñir(pix, tono, sat_min, sat_mult, luz=1.0, oscuro=0.16):
    """Cambia el color de una textura conservando sus sombras; lo muy oscuro y lo blanco (ojos) queda igual."""
    import colorsys
    out = []
    for fila in pix:
        nueva = []
        for (r, g, b, a) in fila:
            if a == 0:
                nueva.append((r, g, b, a)); continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < oscuro or (s < 0.12 and v > 0.92):  # ojos: lo negro y lo blanco no se tine
                nueva.append((r, g, b, a)); continue
            s = min(1.0, sat_min + s * sat_mult); v = min(1.0, v * luz)
            rr, gg, bb = colorsys.hsv_to_rgb(tono, s, v)
            nueva.append((round(rr * 255), round(gg * 255), round(bb * 255), a))
        out.append(nueva)
    return out


# Variantes raras (ideas de Actions & Stuff): salen solas de vez en cuando, o con su etiqueta.
# Mobs que ni Fresh Animations ni sus extensiones tocan con reglas propias (si no, se pisarian).
RARAS = [
    # (carpeta/mob, textura de FA, tono, sat_min, sat_mult, luz, nombres, una de cada N)
    ("dolphin", "dolphin/dolphin.png", 0.95, 0.32, 0.5, 1.06, "bubblegum|chicle", 100),   # delfin rosado, 1%
    ("allay", "allay/allay.png", 0.12, 0.60, 0.4, 1.0, "goldie|dorada|dorado", 10),        # allay dorado, 10%
]


def textura_ext(ruta):
    """Una textura de las extensiones de Fresh Animations (las que estan activas encima de FA)."""
    cache = os.path.join(BASE, ".cache", "FA+All_Extensions-v1.9.2.zip")
    if not os.path.exists(cache):
        url = "https://cdn.modrinth.com/data/YAVTU8mK/versions/R5ZGSF8A/FA%2BAll_Extensions-v1.9.2.zip"
        open(cache, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "texturas-server"}), timeout=60).read())
    return leer_png(zipfile.ZipFile(cache).read("assets/minecraft/textures/entity/" + ruta))


def es_enredadera(c):
    """Pixeles verdes o amarillos de las enredaderas y flores del golem."""
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    return c[3] > 0 and s > 0.3 and 0.1 < h < 0.45


# El golem de hierro (de las extensiones de FA, 128x128). Caras de cada caja: la caja (u, v, w, h, d).
GOLEM_CUERPO = (0, 40, 18, 12, 11)
GOLEM_CINTURA = (0, 68, 10, 6, 7)
GOLEM_BRAZOS = ((60, 21, 4, 30, 6), (60, 58, 4, 30, 6))
GOLEM_PIERNAS = ((60, 0, 6, 16, 5), (37, 0, 6, 16, 5))
GOLEM_CABEZA = (0, 0, 8, 10, 8)


def caras(u, v, w, h, d):
    return dict(arriba=(u + d, v, u + d + w, v + d), abajo=(u + d + w, v, u + d + 2 * w, v + d),
                lado1=(u, v + d, u + d, v + d + h), frente=(u + d, v + d, u + d + w, v + d + h),
                lado2=(u + d + w, v + d, u + 2 * d + w, v + d + h), atras=(u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h))


def golem_skips():
    """Skips (Un Show Mas): yeti de pelo blanco grisaceo, pecho sin pelo, barba blanca en el menton.
    El golem ya tiene su forma (alto, brazos enormes, nariz grande): se le cambia el pelaje."""
    import colorsys
    w, h, pix = textura_ext("iron_golem/iron_golem.png")
    azar = random.Random(11)
    out = [list(f) for f in pix]
    for y in range(h):
        for x in range(w):
            c = pix[y][x]
            if c[3] == 0: continue
            if es_enredadera(c):
                out[y][x] = (0, 0, 0, 0); continue          # sin enredaderas
            hh, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
            if v < 0.2:
                continue                                    # ojos y lineas oscuras quedan
            v = min(1.0, 0.30 + v * 0.72)                   # pelo blanco grisaceo, con sus sombras
            r, g, b = colorsys.hsv_to_rgb(0.66, 0.04, v)
            out[y][x] = (round(r * 255), round(g * 255), round(b * 255), 255)
    # Pecho sin pelo: piel gris un poco mas oscura, con los pectorales marcados.
    x0, y0, x1, y1 = caras(*GOLEM_CUERPO)["frente"]
    for y in range(y0, y1):
        for x in range(x0 + 3, x1 - 3):
            if y < y0 + 9:
                tono = (178, 172, 180) if azar.random() < 0.8 else (168, 162, 170)
                out[y][x] = tono + (255,)
    for x in range(x0 + 4, x1 - 4):
        out[y0 + 5][x] = (140, 134, 144, 255)               # linea bajo los pectorales
    for y in range(y0 + 1, y0 + 6):
        out[y][(x0 + x1) // 2] = (146, 140, 150, 255)       # linea al medio del pecho
    # Barba blanca en el menton (las dos filas de abajo de la cara).
    x0, y0, x1, y1 = caras(*GOLEM_CABEZA)["frente"]
    for y in (y1 - 2, y1 - 1):
        for x in range(x0 + 1, x1 - 1):
            out[y][x] = azar.choice([(244, 244, 246), (232, 232, 236), (250, 250, 252)]) + (255,)
    return png(w, h, out)


def golem_traje():
    """Golem con traje (Actions & Stuff lo tiene como "Dapper"): saco negro, camisa blanca y corbata,
    pantalon negro, puños blancos. La cabeza y las manos siguen de hierro."""
    w, h, pix = textura_ext("iron_golem/iron_golem.png")
    out = [list(f) for f in pix]
    azar = random.Random(5)
    NEG = [(28, 28, 34), (34, 34, 40), (24, 24, 30)]
    def pinta(x0, y0, x1, y1, paleta):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if out[y][x][3] or pix[y][x][3]:
                    out[y][x] = azar.choice(paleta) + (255,)
    for y in range(h):                                      # sin enredaderas
        for x in range(w):
            if es_enredadera(out[y][x]): out[y][x] = (0, 0, 0, 0)
    for k, r in caras(*GOLEM_CUERPO).items():
        pinta(*r, NEG)
    x0, y0, x1, y1 = caras(*GOLEM_CUERPO)["frente"]
    medio = (x0 + x1) // 2
    for y in range(y0, y1):                                 # camisa blanca en V y corbata
        ancho = max(0, 3 - (y - y0) // 3)
        for x in range(medio - ancho - 1, medio + ancho + 1):
            out[y][x] = (236, 236, 240, 255)
        if y < y1 - 2:
            out[y][medio - 1] = (150, 24, 32, 255); out[y][medio] = (130, 20, 28, 255)
    for k, r in caras(*GOLEM_CINTURA).items():
        pinta(*r, NEG)
    for pierna in GOLEM_PIERNAS:
        for k, r in caras(*pierna).items():
            if k != "abajo": pinta(*r, NEG)
    for brazo in GOLEM_BRAZOS:                              # mangas hasta 2/3 del brazo, puño blanco
        for k in ("lado1", "frente", "lado2", "atras"):
            x0, y0, x1, y1 = caras(*brazo)[k]
            corte = y0 + 19
            pinta(x0, y0, x1, corte, NEG)
            for x in range(x0, x1): out[corte][x] = (238, 238, 242, 255)
        x0, y0, x1, y1 = caras(*brazo)["arriba"]
        pinta(x0, y0, x1, y1, NEG)
    return png(w, h, out)


def husk_momia():
    """Husk momia (Actions & Stuff, 3%): vendas en dos tonos con rendijas oscuras; los ojos se asoman."""
    w, h, pix = textura_fa("zombie/husk.png")
    TELA = [(222, 208, 172), (206, 190, 152), (230, 218, 186)]
    RENDIJA = (120, 100, 72)
    azar = random.Random(3)
    # Los ojos son manchas oscuras chicas: esas se dejan. Las manchas oscuras grandes (ropa rota,
    # piernas) se vendan igual que el resto.
    oscuro = lambda c: c[3] > 0 and (c[0] + c[1] + c[2]) < 120
    ojos, visto = set(), set()
    for y0 in range(h):
        for x0 in range(w):
            if (x0, y0) in visto or not oscuro(pix[y0][x0]): continue
            grupo, pila = [], [(x0, y0)]; visto.add((x0, y0))
            while pila:
                x, y = pila.pop(); grupo.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visto and oscuro(pix[ny][nx]):
                        visto.add((nx, ny)); pila.append((nx, ny))
            if len(grupo) <= 6: ojos.update(grupo)
    out = []
    for y, fila in enumerate(pix):
        nueva = []
        for x, c in enumerate(fila):
            if c[3] == 0 or (x, y) in ojos:                 # transparente u ojos: igual
                nueva.append(c); continue
            banda = (y + (x // 4)) % 3
            nueva.append((RENDIJA if banda == 2 else azar.choice(TELA)) + (c[3],))
        out.append(nueva)
    return png(w, h, out)


def golem_y_momia(pack):
    carpeta = os.path.join(pack, "assets", "minecraft", "optifine", "random", "entity", "iron_golem")
    os.makedirs(carpeta, exist_ok=True)
    open(os.path.join(carpeta, "iron_golem2.png"), "wb").write(golem_skips())
    open(os.path.join(carpeta, "iron_golem3.png"), "wb").write(golem_traje())
    with open(os.path.join(carpeta, "iron_golem.properties"), "w", encoding="utf-8") as f:
        f.write("# Skips (Un Show Mas) y el golem con traje (idea de Actions & Stuff), por nombre.\n"
                "skins.1=2\nname.1=iregex:skips\nskins.2=3\nname.2=iregex:(dapper|agent|elegante|agente)\n")
    carpeta = os.path.join(pack, "assets", "minecraft", "optifine", "random", "entity", "zombie")
    os.makedirs(carpeta, exist_ok=True)
    open(os.path.join(carpeta, "husk2.png"), "wb").write(husk_momia())
    with open(os.path.join(carpeta, "husk.properties"), "w", encoding="utf-8") as f:
        f.write("# Husk momia (idea de Actions & Stuff): sale sola 3 de cada 100, o con la etiqueta.\n"
                "skins.1=2\nname.1=iregex:(momia|mummy|dusty)\nskins.2=1 2\nweights.2=97 3\n")


def archivo_ext(ruta):
    textura_ext("enderman/enderman.png")  # deja bajado el zip de las extensiones
    z = zipfile.ZipFile(os.path.join(BASE, ".cache", "FA+All_Extensions-v1.9.2.zip"))
    return z.read("assets/minecraft/" + ruta)


# Mobs que las extensiones de FA ya tienen con reglas (Bart, Dave). Un archivo nuestro con el mismo
# nombre reemplaza al de ellas, asi que se juntan: sus reglas siguen igual y se suma la nuestra.
# Si las extensiones cambian sus reglas, esto avisa en vez de pisarlas sin darse cuenta.
REGLAS_EXT = {
    "optifine/random/entity/enderman/enderman.properties": "skins.1=2\nname.1=iregex:Bart\nskins.2=  1 2\nweights.2=50 1",
    "optifine/random/entity/enderman/enderman_eyes.properties": "skins.1=2\nname.1=iregex:Bart\nskins.2=  1 2\nweights.2=50 1",
    "optifine/random/entity/zombie/zombie.properties": "skins.1=2\nname.1=iregex:Dave\nskins.2=1 2\nweights.2=100 1",
}


def reglas_juntas(ruta, suyo, nuestro_nombre, nuestros, de_cada_mil_ellos, de_cada_mil_nuestro, nota):
    actual = archivo_ext(ruta).decode("utf-8").strip().replace("\r", "")
    assert actual == REGLAS_EXT[ruta], f"las extensiones cambiaron {ruta}: revisar antes de juntar"
    normal = 1000 - de_cada_mil_ellos - de_cada_mil_nuestro
    return (f"# {nota}\n# Juntado con las reglas de Fresh Animations Extensions ({suyo}), que siguen igual.\n"
            f"skins.1=2\nname.1=iregex:{suyo}\n"
            f"skins.2=3\nname.2=iregex:({nuestro_nombre})\n"
            f"skins.3=1 2 3\nweights.3={normal} {de_cada_mil_ellos} {de_cada_mil_nuestro}\n")


def ojos_verdes(ruta):
    """El enderman de ojos verdes (Actions & Stuff, 0.3%): lo morado de los ojos pasa a verde."""
    import colorsys
    w, h, pix = leer_png(archivo_ext("textures/entity/" + ruta))
    out = []
    for fila in pix:
        nueva = []
        for (r, g, b, a) in fila:
            hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if a and s > 0.25 and 0.7 < hh < 0.97:
                rr, gg, bb = colorsys.hsv_to_rgb(0.36, s, v)
                nueva.append((round(rr * 255), round(gg * 255), round(bb * 255), a))
            else:
                nueva.append((r, g, b, a))
        out.append(nueva)
    return png(w, h, out)


def zombie_brian():
    """Brian, el zombie rarisimo (Actions & Stuff solo dice "Brian" o "Glare"): version nuestra, con
    lentes de sol oscuros sobre los ojos."""
    try:
        w, h, pix = leer_png(archivo_ext("textures/entity/zombie/zombie.png"))
    except KeyError:
        w, h, pix = textura_fa("zombie/zombie.png")
    out = [list(f) for f in pix]
    LENTE, MARCO = (16, 16, 22, 255), (40, 40, 48, 255)
    # Cara de la cabeza (8x8 en 8,8). Lentes en la fila de los ojos, puente al medio, patillas a los lados.
    for x in range(9, 15):
        out[12][x] = LENTE
    out[11][9] = MARCO; out[11][10] = MARCO; out[11][13] = MARCO; out[11][14] = MARCO
    out[12][11] = MARCO; out[12][12] = MARCO
    out[12][8] = MARCO; out[12][15] = MARCO
    for x in (6, 7): out[12][x] = MARCO        # patilla en un costado (cara de lado 0..8)
    for x in (16, 17): out[12][x] = MARCO      # y en el otro (16..24)
    # Los ojos propios de Fresh Animations (partes aparte, si las tiene): negros, como el vidrio.
    try:
        jem = json.loads(zipfile.ZipFile(os.path.join(BASE, ".cache", "FreshAnimations_v1.10.5.zip"))
                         .read("assets/minecraft/optifine/cem/zombie.jem"))
        def recorrer(p):
            for s in p.get("submodels", []):
                if "eye" in s.get("id", "") or "pupil" in s.get("id", ""):
                    for b in s.get("boxes", []):
                        uv = b.get("uvNorth")
                        if uv:
                            for y in range(int(uv[1]), int(uv[3])):
                                for x in range(int(uv[0]), int(uv[2])):
                                    out[y][x] = LENTE
                recorrer(s)
        for m in jem["models"]:
            recorrer(m)
    except KeyError:
        pass
    return png(w, h, out)


def variantes_que_se_juntan(pack):
    base = os.path.join(pack, "assets", "minecraft")
    def escribir(ruta, texto):
        os.makedirs(os.path.dirname(os.path.join(base, ruta)), exist_ok=True)
        open(os.path.join(base, ruta), "w", encoding="utf-8").write(texto)
    nota = "Enderman de ojos verdes (Actions & Stuff): 3 de cada 1000, o con la etiqueta Verde/Beanie/Green."
    for capa in ("enderman", "enderman_eyes"):
        ruta = f"optifine/random/entity/enderman/{capa}.properties"
        escribir(ruta, reglas_juntas(ruta, "Bart", "verde|beanie|green|ojos verdes", None, 20, 3, nota))
        open(os.path.join(base, f"optifine/random/entity/enderman/{capa}3.png"), "wb").write(ojos_verdes(f"enderman/{capa}.png"))
    ruta = "optifine/random/entity/zombie/zombie.properties"
    escribir(ruta, reglas_juntas(ruta, "Dave", "brian|glare", None, 10, 1,
                                 "Brian, zombie rarisimo con lentes de sol (version nuestra del de Actions & Stuff): 1 de cada 1000."))
    open(os.path.join(base, "optifine/random/entity/zombie/zombie3.png"), "wb").write(zombie_brian())


def variantes_raras(pack):
    golem_y_momia(pack)
    variantes_que_se_juntan(pack)
    for mob, archivo, tono, smin, smult, luz, nombres, cada in RARAS:
        w, h, pix = textura_fa(archivo)
        carpeta = os.path.join(pack, "assets", "minecraft", "optifine", "random", "entity", mob)
        os.makedirs(carpeta, exist_ok=True)
        open(os.path.join(carpeta, mob + "2.png"), "wb").write(png(w, h, teñir(pix, tono, smin, smult, luz)))
        with open(os.path.join(carpeta, mob + ".properties"), "w", encoding="utf-8") as f:
            f.write(f"# Variante rara: sale sola 1 de cada {cada}, o con la etiqueta ({nombres}).\n"
                    f"skins.1=2\nname.1=iregex:({nombres})\nskins.2=1 2\nweights.2={cada - 1} 1\n")


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


# ---------------- props 3D ----------------
# Adornos para los soportes "prop" (plugin Detalles): el objeto se muestra con uno de estos modelos,
# apoyado en la base del soporte. Hechos con texturas del propio Minecraft (nada copiado de otro
# paquete). Medidas en pixeles de bloque (0 a 16); el modelo se apoya en y=0.
def _cubo(desde, hasta, tex, rot=None, caras_tex=None):
    caras = {}
    for d in ("north", "south", "east", "west", "up", "down"):
        caras[d] = {"texture": "#" + ((caras_tex or {}).get(d, tex))}
    e = {"from": list(desde), "to": list(hasta), "faces": caras}
    if rot:
        e["rotation"] = rot
    return e


PROPS = {
    # id: (texturas, elementos)
    "libro": ({"tapa": "block/red_terracotta", "hoja": "block/white_concrete_powder", "lomo": "block/brown_terracotta"}, [
        _cubo((2.5, 0, 4), (13.5, 0.6, 12), "tapa"),
        _cubo((3, 0.6, 4.4), (7.9, 1.4, 11.6), "hoja"),
        _cubo((8.1, 0.6, 4.4), (13, 1.4, 11.6), "hoja"),
        _cubo((7.8, 0.6, 4.2), (8.2, 1.2, 11.8), "lomo"),
    ]),
    "libros": ({"r": "block/red_terracotta", "a": "block/blue_terracotta", "v": "block/green_terracotta",
                "hoja": "block/white_concrete_powder"}, [
        _cubo((3, 0, 5), (12, 2, 11), "r", caras_tex={"north": "hoja", "south": "hoja", "east": "hoja"}),
        _cubo((4, 2, 4.5), (12.5, 3.6, 10.5), "a", {"origin": [8, 2, 8], "axis": "y", "angle": 22.5},
              caras_tex={"north": "hoja", "south": "hoja", "east": "hoja"}),
        _cubo((3.5, 3.6, 5.5), (11, 5, 11), "v", {"origin": [8, 4, 8], "axis": "y", "angle": -22.5},
              caras_tex={"north": "hoja", "south": "hoja", "east": "hoja"}),
    ]),
    "taza": ({"loza": "block/white_terracotta", "cafe": "block/brown_concrete"}, [
        _cubo((6, 0, 6), (10, 4, 10), "loza"),
        _cubo((6.5, 3.6, 6.5), (9.5, 3.9, 9.5), "cafe"),
        _cubo((10, 0.8, 7.5), (11.2, 1.4, 8.5), "loza"),
        _cubo((10.6, 1.4, 7.5), (11.2, 2.8, 8.5), "loza"),
        _cubo((10, 2.8, 7.5), (11.2, 3.4, 8.5), "loza"),
    ]),
    "sopa": ({"plato": "block/white_concrete", "pocillo": "block/stripped_oak_log", "sopa": "block/orange_terracotta"}, [
        _cubo((3.5, 0, 3.5), (12.5, 0.5, 12.5), "plato"),
        _cubo((5.5, 0.5, 5.5), (10.5, 2.6, 10.5), "pocillo"),
        _cubo((6, 2.2, 6), (10, 2.5, 10), "sopa"),
    ]),
    "galletas": ({"plato": "block/white_concrete", "galleta": "item/cookie", "masa": "block/brown_terracotta"}, [
        _cubo((3.5, 0, 3.5), (12.5, 0.5, 12.5), "plato"),
        _cubo((4.5, 0.5, 4.5), (8, 1.1, 8), "masa", caras_tex={"up": "galleta"}),
        _cubo((8, 0.5, 5), (11.5, 1.1, 8.5), "masa", caras_tex={"up": "galleta"}),
        _cubo((6, 1.1, 6.5), (9.5, 1.7, 10), "masa", caras_tex={"up": "galleta"}),
    ]),
    "frasco": ({"vidrio": "block/glass", "tapa": "block/spruce_planks", "miel": "block/honey_block_side"}, [
        _cubo((6, 0, 6), (10, 5, 10), "vidrio"),
        _cubo((6.4, 0.1, 6.4), (9.6, 2.6, 9.6), "miel"),
        _cubo((5.8, 5, 5.8), (10.2, 5.8, 10.2), "tapa"),
    ]),
    "jarra": ({"loza": "block/white_concrete", "leche": "block/white_wool", "asa": "block/light_gray_concrete"}, [
        _cubo((5.5, 0, 5.5), (10.5, 6, 10.5), "loza"),
        _cubo((6, 5.7, 6), (10, 5.9, 10), "leche"),
        _cubo((4.8, 5, 7.3), (5.5, 6, 8.7), "loza"),
        _cubo((10.5, 1.5, 7.4), (11.7, 2.1, 8.6), "asa"),
        _cubo((11.1, 2.1, 7.4), (11.7, 4.4, 8.6), "asa"),
        _cubo((10.5, 4.4, 7.4), (11.7, 5, 8.6), "asa"),
    ]),
    "pluma": ({"tinta": "block/black_concrete", "pluma": "block/white_wool", "papel": "block/white_concrete_powder"}, [
        _cubo((3, 0, 4), (11, 0.3, 12), "papel"),
        _cubo((10, 0, 9), (13, 2.2, 12), "tinta"),
        _cubo((11.2, 2.2, 10.2), (11.8, 9, 10.8), "pluma", {"origin": [11.5, 2.2, 10.5], "axis": "x", "angle": -22.5}),
    ]),
    "telescopio": ({"base": "block/dark_oak_planks", "tubo": "block/copper_block", "lente": "block/black_concrete"}, [
        _cubo((6, 0, 6), (10, 1, 10), "base"),
        _cubo((7.5, 1, 7.5), (8.5, 7, 8.5), "base"),
        _cubo((2.5, 7, 7), (13.5, 9, 9), "tubo", {"origin": [8, 8, 8], "axis": "z", "angle": 22.5},
              caras_tex={"west": "lente", "east": "lente"}),
    ]),
    "disco": ({"vinilo": "block/black_concrete", "etiqueta": "block/red_concrete", "base": "block/oak_planks"}, [
        _cubo((4.5, 0, 6.5), (11.5, 1, 9.5), "base"),
        _cubo((3, 1, 7.6), (13, 11, 8.4), "vinilo"),
        _cubo((6.5, 4.5, 7.5), (9.5, 7.5, 8.5), "etiqueta"),
    ]),
}


def props(pack):
    for pid, (texturas, elementos) in PROPS.items():
        modelo = {
            "textures": {**{k: "minecraft:" + v for k, v in texturas.items()},
                         "particle": "minecraft:" + next(iter(texturas.values()))},
            "elements": elementos,
            # "fixed" es como lo muestra el adorno (tamano real, sin girar); "gui" por si alguien lo ve en un menu.
            "display": {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
                        "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.8, 0.8, 0.8]}},
        }
        ruta = os.path.join(pack, "assets", "amigos", "models", "item", "prop", pid + ".json")
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        json.dump(modelo, open(ruta, "w", encoding="utf-8"), indent=1)
        item = os.path.join(pack, "assets", "amigos", "items", "prop_" + pid + ".json")
        os.makedirs(os.path.dirname(item), exist_ok=True)
        json.dump({"model": {"type": "minecraft:model", "model": "amigos:item/prop/" + pid}},
                  open(item, "w", encoding="utf-8"), indent=1)


def armar(version):
    pack = os.path.join(BASE, "pack")
    secretos_por_nombre(pack)
    variantes_raras(pack)
    props(pack)
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
