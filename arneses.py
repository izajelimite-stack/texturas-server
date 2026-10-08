"""Arneses del happy ghast con temas: cada color tiene su propio diseno.

La idea de un tema por color viene de Actions & Stuff; el dibujo es nuestro, hecho aqui pixel a pixel.

La textura del arnes es de 128x128 (el doble que el modelo de 64). La caja del cuerpo, de
16x16x16, queda desplegada asi, en pixeles:
  arriba   x 32..63, y 0..31  (fila 0 = atras, fila 31 = adelante; columna 0 = lado derecho)
  abajo    x 64..95, y 0..31
  lados    y 32..63: derecho x 0..31 (de atras hacia adelante), frente x 32..63,
           izquierdo x 64..95 (de adelante hacia atras), espalda x 96..127.
Los lados forman una franja continua: x 127 sigue en x 0.
Las antiparras son una caja de 16x5x5 en (0, 64): el frente va en x 10..41, y 74..83, y cuando
alguien lo monta bajan justo sobre los ojos del ghast.
El frente del cuerpo queda casi libre para no tapar la cara del ghast.
"""
import math

T = 128
FRENTE = range(32, 64)
MANTA_Y = 35          # primera fila de la manta (arriba queda el borde de la silla)


def h(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


def mezcla(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def luz(c, f):
    return tuple(max(0, min(255, int(round(c[i] * f)))) for i in range(3)) + (255,)


def ruido(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536


class Lienzo:
    def __init__(self):
        self.p = [[(0, 0, 0, 0)] * T for _ in range(T)]

    def pon(self, x, y, c):
        if c and 0 <= x < T and 0 <= y < T:
            self.p[y][x] = c

    def hay(self, x, y):
        return 0 <= x < T and 0 <= y < T and self.p[y][x][3] > 0

    def dibujo(self, x, y, filas, paleta, espejo=False):
        for j, fila in enumerate(filas):
            if espejo:
                fila = fila[::-1]
            for i, ch in enumerate(fila):
                if ch in paleta:
                    self.pon(x + i, y + j, paleta[ch])


def es_lado(x):
    return x not in FRENTE


def a_esquina_frente(x):
    """Distancia (en columnas) a la esquina con el frente; None en la espalda y el frente."""
    if 0 <= x < 32:
        return 31 - x
    if 64 <= x < 96:
        return x - 64
    return None


# ---------------- piezas comunes ----------------

def silla(l, pal, costura=None, relleno=None):
    """pal = [oscuro, medio, claro, brillo]. relleno(i, j) da el color del centro (o None)."""
    for j in range(32):
        for i in range(32):
            d = min(i, j, 31 - i, 31 - j)
            if d == 0:
                c = pal[0]
            elif d == 1:
                c = pal[1]
            else:
                c = relleno(i, j) if relleno else None
                if c is None:
                    c = mezcla(pal[2], pal[1] if ruido(i, j, 7) < 0.5 else pal[3], ruido(i, j, 3) * 0.35)
                if costura and d == 3 and (i + j) % 3 != 0:
                    c = costura
            l.pon(32 + i, j, c)
    # borde de la silla que cae un poco por los lados (en el frente, solo una linea fina)
    for x in range(T):
        filas = (pal[1], pal[0]) if x in FRENTE else (pal[1], mezcla(pal[1], pal[0], 0.5), pal[0])
        for k, c in enumerate(filas):
            l.pon(x, 32 + k, c)


def manta(l, color, largo, ribete=None, oscurecer_borde=True):
    """color(x, f, n): color de la fila f (0 = arriba) en la columna x; largo(x): filas de manta."""
    alto = {}
    for x in range(T):
        if not es_lado(x):
            continue
        n = largo(x)
        d = a_esquina_frente(x)
        if d is not None and d < 6:          # la manta sube suave hacia la cara del ghast
            n = min(n, 5 + d * 2)
        alto[x] = n
        for f in range(n):
            c = color(x, f, n)
            if ribete and n - 4 <= f < n - 2:
                c = ribete[(f - (n - 4)) % len(ribete)]
            if oscurecer_borde and f == n - 1:
                c = luz(c, 0.72)
            l.pon(x, MANTA_Y + f, c)
    return alto


def correas(l, cuero, metal, hebilla_y=52):
    """Una correa por cada lado que pasa por debajo de la panza, con su hebilla."""
    for x0 in (14, 78):
        for y in range(MANTA_Y, 64):
            for k, c in enumerate((cuero[0], cuero[2], cuero[1], cuero[0])):
                l.pon(x0 + k, y, c)
        for y in range(hebilla_y, hebilla_y + 5):
            for x in range(x0 - 1, x0 + 5):
                borde = y in (hebilla_y, hebilla_y + 4) or x in (x0 - 1, x0 + 4)
                if borde:
                    l.pon(x, y, metal[1] if (y == hebilla_y or x == x0 - 1) else metal[0])
        l.pon(x0 + 1, hebilla_y + 2, metal[1])       # la punta del pasador
    for x in range(64, 96):                          # por la panza, de lado a lado
        for k, c in enumerate((cuero[0], cuero[2], cuero[1], cuero[0])):
            l.pon(x, 14 + k, c)


def antiparras(l, marco, vidrio, correa):
    """marco = [oscuro, medio, claro]; vidrio = [base, brillo]; correa = [oscuro, medio]."""
    for x in list(range(0, 14)) + list(range(39, 52)):
        for y, c in zip(range(77, 81), (correa[0], correa[1], correa[1], correa[0])):
            l.pon(x, y, c)
    for x0 in (13, 28):
        for y in range(74, 84):
            for x in range(x0, x0 + 12):
                esquina = (x in (x0, x0 + 11)) and (y in (74, 83))
                if esquina:
                    continue
                if x in (x0, x0 + 11) or y in (74, 83):
                    c = marco[0]
                elif x in (x0 + 1, x0 + 10) or y in (75, 82):
                    c = marco[2] if (y == 75 or x == x0 + 1) else marco[1]
                else:
                    gx, gy = x - x0 - 2, y - 76
                    c = vidrio[1] if (gx + gy in (1, 2) or (gx, gy) == (6, 4)) else vidrio[0]
                l.pon(x, y, c)
    for x in range(25, 28):                          # puente entre los lentes
        for y, c in zip(range(77, 80), (marco[2], marco[1], marco[0])):
            l.pon(x, y, c)


def frontal(l, y0, filas, paleta):
    """Dibuja algo centrado en el frente de las antiparras (x 10..41)."""
    ancho = len(filas[0])
    l.dibujo(10 + (32 - ancho) // 2, y0, filas, paleta)


def en_espalda(l, y0, filas, paleta):
    ancho = len(filas[0])
    l.dibujo(96 + (32 - ancho) // 2, y0, filas, paleta)


def en_lados(l, x_der, y0, filas, paleta):
    """Lo mismo en los dos costados, en espejo: x_der es la columna en el lado derecho (0..31)."""
    ancho = len(filas[0])
    l.dibujo(x_der, y0, filas, paleta)
    l.dibujo(64 + (31 - x_der) - (ancho - 1), y0, filas, paleta, espejo=True)


def en_silla(l, i0, j0, filas, paleta):
    l.dibujo(32 + i0, j0, filas, paleta)


def voronoi(i, j, paso, semilla):
    """Distancias al centro mas cercano y al segundo (celdas para escamas y caparazones)."""
    mejores = []
    ci, cj = i // paso, j // paso
    for a in range(ci - 1, ci + 2):
        for b in range(cj - 1, cj + 2):
            px = (a + 0.2 + 0.6 * ruido(a, b, semilla)) * paso
            py = (b + 0.2 + 0.6 * ruido(a, b, semilla + 1)) * paso
            mejores.append(math.hypot(i - px, j - py))
    mejores.sort()
    return mejores[0], mejores[1]


CUERO = [h("#3b2414"), h("#5a3820"), h("#7a4d2c"), h("#94643a")]
CORREA = [h("#3b2414"), h("#5a3820"), h("#7a4d2c")]
PLATA = [h("#5d5f68"), h("#c2c5cc")]
ORO = [h("#8e6512"), h("#f0cc55")]
MARCO = [h("#2e1c10"), h("#4f321c"), h("#74502f")]
VIDRIO = [h("#9fd3e0"), h("#eaf8fb")]


# ---------------- los 16 temas ----------------

def lana():
    """Blanco: gorro de lana con pompon."""
    l = Lienzo()
    blancos = [h("#a39d92"), h("#cfc9bd"), h("#efebe2"), h("#fbfaf6")]

    def tejido(i, j):
        luzv = (j + (i % 2)) % 2 == 0
        c = blancos[3] if luzv else blancos[2]
        if i % 4 in (1, 2) and j % 2:
            c = blancos[1]
        return c
    silla(l, blancos, relleno=tejido)
    pompon = [h("#9e2f2b"), h("#c8463e"), h("#e5655b"), h("#f59a8f")]
    for j in range(10, 22):
        for i in range(10, 22):
            d = math.hypot(i - 15.5, j - 15.5)
            if d < 5.6 + ruido(i, j, 5) * 0.8:
                t = (d / 6) - (15.5 - j) * 0.04 - (15.5 - i) * 0.03
                k = 3 if t < 0.15 else 2 if t < 0.5 else 1 if t < 0.85 else 0
                l.pon(32 + i, j, pompon[k])
    lanas = [h("#f3ecdd"), h("#e3d8c2"), h("#cfc0a3"), h("#b3a283")]

    def rulos(x, f, n):
        r = ruido(x // 2, (f + (x // 2) % 2) // 2, 11)
        k = 0 if r < 0.35 else 1 if r < 0.7 else 2
        if (x + f) % 5 == 0:
            k = 3
        return lanas[k]
    manta(l, rulos, lambda x: 14 + round(3 * math.sqrt(max(0, 1 - ((x % 8 - 3.5) / 4) ** 2))),
          ribete=[h("#c8463e"), h("#9e2f2b")])
    correas(l, [h("#6b4a2f"), h("#8f6743"), h("#b08559")], PLATA)
    antiparras(l, MARCO, VIDRIO, [h("#4f321c"), h("#74502f")])
    return l


def calabaza():
    """Naranjo: calabaza, con la cara tallada en la espalda."""
    l = Lienzo()
    nar = [h("#8a3d0c"), h("#c2610f"), h("#e3861a"), h("#f5a53a")]

    def gajos(i, j):
        a = math.atan2(j - 15.5, i - 15.5)
        fr = (a / (2 * math.pi) * 10) % 1
        r = math.hypot(i - 15.5, j - 15.5)
        if r < 2.6:
            return None
        if fr < 0.12 or fr > 0.92:
            return nar[1]
        return mezcla(nar[3], nar[2], r / 15)
    silla(l, nar, relleno=gajos)
    en_silla(l, 13, 13, [".gG.", "gGGg", "gGgg", ".gg.", "..lL", "...l"],
             {"g": h("#4d5a22"), "G": h("#6f7f30"), "l": h("#4f7a28"), "L": h("#76a33a")})
    tonos = [h("#a8480b"), h("#c8600f"), h("#e57d1a"), h("#f39a33")]

    def costillas(x, f, n):
        k = x % 6
        c = tonos[[0, 1, 2, 3, 2, 1][k]]
        return luz(c, 1 - f / n * 0.25)
    manta(l, costillas, lambda x: 15 + round(2 * math.sin(math.pi * (x % 6) / 6)),
          ribete=[h("#4f7a28"), h("#76a33a")])
    en_espalda(l, 37, [
        "...k........k...",
        "..kyk......kyk..",
        ".kyyyk....kyyyk.",
        "kkkkkkk..kkkkkkk",
        "................",
        "kk............kk",
        "kykk.kkkkkk.kkyk",
        "kyyykyyyyyykyyyk",
        ".kyyyyykkyyyyyk.",
        "..kkkkk..kkkkk..",
    ], {"k": h("#3a1906"), "y": h("#ffc93d")})
    correas(l, CORREA, PLATA)
    antiparras(l, MARCO, VIDRIO, [h("#4d5a22"), h("#6f7f30")])
    return l


def shulker():
    """Magenta: caparazon de shulker, con uno asomandose atras."""
    l = Lienzo()
    mor = [h("#5a2758"), h("#86407f"), h("#a8579f"), h("#c476b8")]

    def placas(i, j):
        d = min(i, j, 31 - i, 31 - j)
        if d % 5 == 4:
            return mor[0]
        return mezcla(mor[3], mor[2], (d % 5) / 4)
    silla(l, mor, relleno=placas)

    def caparazon(x, f, n):
        if f % 5 == 4 or x % 16 == 0:
            return h("#4a1f48")
        return mezcla(h("#c071b4"), h("#8e4486"), (f % 5) / 4)
    manta(l, caparazon, lambda x: 16, ribete=None)
    en_espalda(l, 41, [
        "kkkkkkkkkkkkkk",
        "kyyYYYYYYYYyyk",
        "kyykkyyyykkyyk",
        "kyyyyyyyyyyyyk",
        "kkkkkkkkkkkkkk",
    ], {"k": h("#2a0f29"), "y": h("#d9c98a"), "Y": h("#ece0a8")})
    correas(l, [h("#3a1838"), h("#5a2a56"), h("#77407a")], PLATA)
    antiparras(l, [h("#3a1838"), h("#5a2a56"), h("#8a4f86")], [h("#e7c6f0"), h("#fbefff")],
               [h("#3a1838"), h("#5a2a56")])
    return l


def allay():
    """Celeste: allay, con alitas a los lados y una nota musical arriba."""
    l = Lienzo()
    cel = [h("#3f7fa8"), h("#62a6cf"), h("#8ccbec"), h("#c5ecff")]

    def brillos(i, j):
        if ruido(i, j, 21) > 0.97:
            return h("#ffffff")
        return None
    silla(l, cel, costura=h("#e9f8ff"), relleno=brillos)
    en_silla(l, 12, 12, [
        "..nnnnnn",
        "..nnnnnn",
        "..n....n",
        "..n....n",
        "..n....n",
        ".nn...nn",
        "nnn..nnn",
        ".n....n.",
    ], {"n": h("#1f4f7a")})

    def cielo(x, f, n):
        c = mezcla(h("#a9e2ff"), h("#5fb0e6"), f / n)
        if ruido(x, f, 23) > 0.96:
            c = h("#ffffff")
        return c
    manta(l, cielo, lambda x: 15 + round(1.5 * math.sin(x / 3)), ribete=[h("#e9f8ff"), h("#c2e6fa")])
    ala = [
        "......ooo..",
        "....oowwwo.",
        "...owwwwwbo",
        "..owwwwwbbo",
        ".owwwwbbbo.",
        ".owwwbbbo..",
        "owwwbbbo...",
        "owwbbo.....",
        "obbo.......",
        ".oo........",
    ]
    en_lados(l, 2, 37, ala, {"o": h("#2f6f99"), "w": h("#ffffff"), "b": h("#dff4ff")})
    correas(l, [h("#2f6f99"), h("#4f98c4"), h("#87c6ea")], PLATA)
    antiparras(l, [h("#2f6f99"), h("#4f98c4"), h("#87c6ea")], [h("#d6f4ff"), h("#ffffff")],
               [h("#2f6f99"), h("#4f98c4")])
    return l


def abeja():
    """Amarillo: abeja, con panal arriba, rayas, alas y aguijon."""
    l = Lienzo()
    miel = [h("#7a4d06"), h("#b07210"), h("#e8a721"), h("#ffd45c")]

    def panal(i, j):
        r = j // 5
        c = (i + (r % 2) * 3) % 6
        if j % 5 == 0 and c in (1, 2, 3, 4):
            return miel[1]
        if j % 5 != 0 and c == 0:
            return miel[1]
        return miel[3] if (j % 5 == 1 and c in (2, 3)) else miel[2]
    silla(l, miel, relleno=panal)

    def rayas(x, f, n):
        negro = (f // 4) % 2 == 1
        base = h("#2a2420") if negro else h("#f2c230")
        return luz(base, 0.92 + ruido(x, f, 31) * 0.12)
    alto = manta(l, rayas, lambda x: 16)
    ala = [
        "..oooo....",
        ".owwwwo...",
        "owwvwwwo..",
        "owwwvwwwo.",
        ".owwwvwwo.",
        "..owwwwwo.",
        "...oowwo..",
        ".....oo...",
    ]
    en_lados(l, 3, 36, ala, {"o": h("#8e9daa"), "w": h("#eef6fb"), "v": h("#c3d0da")})
    fondo = MANTA_Y + alto[111]
    for k, ancho in enumerate((4, 2, 2, 1)):
        for x in range(112 - ancho // 2 - (ancho % 2), 112 + ancho // 2):
            l.pon(x, fondo + k, h("#2a2420"))
    correas(l, [h("#1c1816"), h("#2e2824"), h("#433a33")], ORO)
    antiparras(l, [h("#1c1816"), h("#2e2824"), h("#4a403a")], [h("#f6c445"), h("#fff1b8")],
               [h("#1c1816"), h("#2e2824")])
    return l


def tortuga():
    """Lima: caparazon de tortuga."""
    l = Lienzo()
    ver = [h("#2f5a1f"), h("#4c8a2e"), h("#6fb33f"), h("#9bd35c")]

    def escudos(i, j):
        d1, d2 = voronoi(i, j, 11, 41)
        if d2 - d1 < 1.3:
            return h("#3b4f1c")
        return mezcla(ver[3], ver[1], d1 / 8)
    silla(l, ver, relleno=escudos)

    def escamas(x, f, n):
        d1, d2 = voronoi(x, f, 6, 43)
        if d2 - d1 < 1.0:
            return h("#2f5a1f")
        return mezcla(h("#8fcc52"), h("#4f9430"), d1 / 4)
    manta(l, escamas, lambda x: 14 + round(2 * math.sqrt(max(0, 1 - ((x % 7 - 3) / 3.5) ** 2))),
          ribete=[h("#d1d46e"), h("#a5ad48")])
    correas(l, [h("#3a3518"), h("#5a5224"), h("#7a7032")], PLATA)
    antiparras(l, [h("#3a3518"), h("#5a5224"), h("#7a7032")], [h("#c9f0d0"), h("#f2fff4")],
               [h("#3a3518"), h("#5a5224")])
    return l


def ajolote():
    """Rosado: ajolote, con branquias a los lados."""
    l = Lienzo()
    ros = [h("#b0577a"), h("#d97a9e"), h("#f2a5c0"), h("#ffd0e0")]

    def manchas(i, j):
        if ruido(i // 2, j // 2, 51) > 0.86:
            return h("#e58cb0")
        return None
    silla(l, ros, relleno=manchas)

    def piel(x, f, n):
        c = mezcla(h("#f7b3cb"), h("#e98fb1"), f / n)
        if ruido(x // 2, f // 2, 53) > 0.88:
            c = h("#e07aa3")
        return c
    manta(l, piel, lambda x: 15 + (1 if x % 4 in (1, 2) else -1 if x % 4 == 3 else 0),
          ribete=[h("#c2336f"), h("#e0558f")])
    for x0, paso in ((29, -1), (66, 1)):              # tres plumas en abanico, cerca de la cara
        for ang in (-0.6, 0.0, 0.6):
            dx, dy = math.cos(ang) * paso, math.sin(ang)
            for k in range(12):
                x, y = round(x0 + dx * k), round(41 + dy * k * 1.3)
                l.pon(x, y, h("#9c1c50"))
                l.pon(x, y + 1, h("#c2336f"))
                if k >= 3 and k % 2 == 1:
                    l.pon(x, y - 1, h("#ff86b8"))
                    l.pon(x, y + 2, h("#ff86b8"))
    correas(l, [h("#7a2f4c"), h("#9c4366"), h("#b85d80")], PLATA)
    antiparras(l, [h("#7a2f4c"), h("#c2336f"), h("#e0558f")], [h("#d8f2ff"), h("#ffffff")],
               [h("#7a2f4c"), h("#9c4366")])
    return l


def minero():
    """Gris: minero, con lona, cinturon de herramientas y linterna en las antiparras."""
    l = Lienzo()
    gri = [h("#2e3033"), h("#45484d"), h("#5d6168"), h("#7a7f86")]

    def lona(i, j):
        d = min(i, j, 31 - i, 31 - j)
        if d == 2 and (i + j) % 5 == 0:
            return h("#c7cbd1")                       # remaches
        return gri[2] if (i + j) % 2 else luz(gri[2], 1.08)
    silla(l, gri, relleno=lona)

    def tela(x, f, n):
        c = h("#6b6f75") if (x + f) % 2 else h("#73777d")
        if 100 <= x <= 108 and 2 <= f <= 8:
            c = h("#5a5e64") if (x + f) % 2 else h("#62666c")      # parche cosido
            if x in (100, 108) or f in (2, 8):
                c = h("#8d9197") if (x + f) % 2 else h("#5a5e64")
        return c
    manta(l, tela, lambda x: 16, ribete=[h("#5a3820"), h("#7a4d2c")])
    en_espalda(l, 37, [
        "..ddddd..",
        ".dmlllmd.",
        "dm.dhd.md",
        "d..dhd..d",
        "....h....",
        "....h....",
        "....h....",
        "....d....",
    ], {"d": h("#2f3236"), "m": h("#8f959b"), "l": h("#d5d9dd"), "h": h("#7a5232")})
    correas(l, [h("#26282b"), h("#3a3d41"), h("#53575c")], PLATA)
    antiparras(l, [h("#26282b"), h("#3a3d41"), h("#5d6168")], [h("#cfe3ea"), h("#ffffff")],
               [h("#26282b"), h("#3a3d41")])
    frontal(l, 74, [
        ".ggg.",
        "gyYyg",
        "gYWYg",
        "gyYyg",
        ".ggg.",
    ], {"g": h("#4a4d52"), "y": h("#f2c94c"), "Y": h("#ffe680"), "W": h("#fffbe6")})
    return l


def rana():
    """Gris claro: rana templada, con ojos de rana arriba y en los lentes."""
    l = Lienzo()
    cre = [h("#8f877a"), h("#b9b0a1"), h("#ddd4c4"), h("#f2ece0")]

    def piel(i, j):
        d1, _ = voronoi(i, j, 9, 61)
        if d1 < 1.8:
            return h("#d29a62")
        return None
    silla(l, cre, relleno=piel)
    ojo = [
        ".ccccc.",
        "cgggggc",
        "ckkkkkc",
        "cgggggc",
        ".ccccc.",
    ]
    pal = {"c": h("#8f877a"), "g": h("#d9b44a"), "k": h("#1f1f1f")}
    en_silla(l, 5, 24, ojo, pal)
    en_silla(l, 20, 24, ojo, pal)

    def manchas(x, f, n):
        d1, _ = voronoi(x, f, 7, 63)
        c = mezcla(h("#efe7d8"), h("#d8cdb9"), f / n)
        if d1 < 1.6:
            c = h("#d29a62")
        return c
    manta(l, manchas, lambda x: 15 + round(math.sin(x / 2.5)), ribete=[h("#e0a873"), h("#c98a55")])
    correas(l, [h("#5c554c"), h("#7a7266"), h("#9a9183")], PLATA)
    antiparras(l, [h("#5c554c"), h("#8f877a"), h("#b9b0a1")], [h("#e9c25a"), h("#fff0b0")],
               [h("#5c554c"), h("#7a7266")])
    for x0 in (15, 30):                               # pupila de rana en cada lente
        for x in range(x0 + 1, x0 + 7):
            l.pon(x, 78, h("#1f1f1f"))
            l.pon(x, 79, h("#1f1f1f"))
    return l


def warden():
    """Cian: warden, con sculk, puntos que brillan y el pecho con costillas arriba."""
    l = Lienzo()
    osc = [h("#0b1f26"), h("#123540"), h("#1b4a57"), h("#2a6a78")]

    def sculk(i, j):
        return osc[1] if ruido(i // 2, j // 2, 71) < 0.5 else osc[2]
    silla(l, osc, relleno=sculk)
    en_silla(l, 9, 10, [
        "......rr......",
        "..rrrrrrrrrr..",
        ".r....rr....r.",
        "..rrrr..rrrr..",
        ".r....hh....r.",
        "..rrr.hH.rrr..",
        ".r...hhhh...r.",
        "..rr..hh..rr..",
        ".r....rr....r.",
        "..rrrrrrrrrr..",
        "......rr......",
    ], {"r": h("#3fd8e0"), "h": h("#7ff7ff"), "H": h("#ffffff")})

    def piel(x, f, n):
        c = h("#0f2a33") if ruido(x // 2, f // 2, 73) < 0.55 else h("#173d48")
        r = ruido(x, f, 75)
        if r > 0.965:
            c = h("#9ffcff")
        elif r > 0.93:
            c = h("#3fd8e0")
        return c
    manta(l, piel, lambda x: 13 + int(ruido(x, 0, 77) * 5), ribete=None)
    correas(l, [h("#081418"), h("#0f2128"), h("#17323b")], [h("#1f6b77"), h("#4de2e6")])
    antiparras(l, [h("#081418"), h("#123540"), h("#1f6b77")], [h("#5ff0f2"), h("#d9ffff")],
               [h("#081418"), h("#0f2128")])
    return l


def enderman():
    """Morado: enderman, negro con particulas moradas y sus ojos en la espalda."""
    l = Lienzo()
    neg = [h("#0e0b12"), h("#1a1520"), h("#262030"), h("#3a3046")]

    def particulas(i, j):
        r = ruido(i, j, 81)
        if r > 0.97:
            return h("#e08bff")
        if r > 0.94:
            return h("#9a48d6")
        return neg[2] if ruido(i, j, 82) < 0.6 else neg[1]
    silla(l, neg, relleno=particulas)

    def tela(x, f, n):
        r = ruido(x, f, 83)
        if r > 0.97:
            return h("#e08bff")
        if r > 0.94:
            return h("#9a48d6")
        return h("#16121b") if ruido(x, f, 84) < 0.5 else h("#1f1a26")
    manta(l, tela, lambda x: 17, ribete=[h("#8e3ccf"), h("#c06bff")])
    en_espalda(l, 40, [
        "ppppppp......ppppppp",
        "pPPPPPp......pPPPPPp",
    ], {"p": h("#b54fff"), "P": h("#f0b3ff")})
    correas(l, [h("#0e0b12"), h("#1f1a26"), h("#33283f")], [h("#5b3d7a"), h("#b98ae6")])
    antiparras(l, [h("#0e0b12"), h("#1f1a26"), h("#3a3046")], [h("#d07bff"), h("#f6d9ff")],
               [h("#0e0b12"), h("#1f1a26")])
    return l


def noche():
    """Azul: cielo de noche, con estrellas y una luna en la espalda."""
    l = Lienzo()
    azu = [h("#141c45"), h("#1f2b66"), h("#2c3d8a"), h("#3f55b0")]

    def estrellas(i, j):
        if ruido(i, j, 91) > 0.975:
            return h("#f6e7a6")
        return azu[2] if ruido(i, j, 92) < 0.7 else azu[1]
    silla(l, azu, costura=h("#e8c45a"), relleno=estrellas)

    def cielo(x, f, n):
        c = mezcla(h("#24317a"), h("#121a47"), f / n)
        r = ruido(x, f, 93)
        if r > 0.975:
            c = h("#ffffff")
        elif r > 0.955:
            c = h("#f6e7a6")
        return c
    manta(l, cielo, lambda x: 15 + round(2 * math.sqrt(max(0, 1 - ((x % 8 - 3.5) / 4) ** 2))),
          ribete=[h("#e8c45a"), h("#b8902f")])
    en_espalda(l, 37, [
        "...mmm..",
        ".mmm....",
        "mmn.....",
        "mmn.....",
        "mmn.....",
        "mmmn....",
        ".mmmm...",
        "...mmm..",
    ], {"m": h("#f6e7a6"), "n": h("#d9bf62")})
    correas(l, [h("#0e1433"), h("#1a2352"), h("#2a3670")], ORO)
    antiparras(l, [h("#0e1433"), h("#1f2b66"), h("#3f55b0")], [h("#c7d8ff"), h("#ffffff")],
               [h("#0e1433"), h("#1a2352")])
    return l


def creaking():
    """Cafe: creaking, de corteza con raices y ojos naranjos que brillan."""
    l = Lienzo()
    cor = [h("#2b211c"), h("#3e312a"), h("#54443a"), h("#6b5849")]

    def corteza(i, j):
        if 18 <= i <= 21 and 9 <= j <= 12:
            return h("#ffad4a") if (i, j) in ((19, 10), (20, 11)) else h("#e0752a")   # resina
        r = ruido(i // 2, j // 5, 101)
        return cor[1] if r < 0.33 else cor[2] if r < 0.75 else cor[3]
    silla(l, cor, relleno=corteza)

    def tronco(x, f, n):
        r = ruido(x // 2, f // 6, 103)
        return h("#3a2e27") if r < 0.3 else h("#4a3c33") if r < 0.7 else h("#5e4d42")
    alto = manta(l, tronco, lambda x: 13 + int(ruido(x, 1, 105) * 4), ribete=None)
    for x in range(T):                                # raices finas que bajan
        if x in alto and ruido(x, 2, 107) > 0.86:
            for k in range(2 + int(ruido(x, 3, 109) * 4)):
                l.pon(x, MANTA_Y + alto[x] + k, h("#2b211c"))
    en_espalda(l, 40, [
        "oO..........Oo",
        "OY..........YO",
    ], {"o": h("#e0752a"), "O": h("#ff9a3c"), "Y": h("#ffe0a0")})
    correas(l, [h("#1f1814"), h("#33281f"), h("#4a3b2e")], [h("#3a3a3a"), h("#7a7a7a")])
    antiparras(l, [h("#1f1814"), h("#3e312a"), h("#6b5849")], [h("#ff9a3c"), h("#ffd9a0")],
               [h("#1f1814"), h("#33281f")])
    return l


def hojas():
    """Verde: hojas, con musgo y flores arriba."""
    l = Lienzo()
    mus = [h("#2d4a1a"), h("#3f6624"), h("#55842f"), h("#73a640")]
    flores = [h("#f29ac2"), h("#f7d54a"), h("#f4f4f4"), h("#9ec9ff")]

    def musgo(i, j):
        r = ruido(i, j, 111)
        if r > 0.965:
            return flores[int(ruido(i, j, 112) * 4)]
        return mus[2] if ruido(i // 2, j // 2, 113) < 0.6 else mus[3]
    silla(l, mus, relleno=musgo)
    verdes = [h("#2f5a1d"), h("#3c6e25"), h("#4e8a2e"), h("#62a437")]

    def follaje(x, f, n):
        d1, d2 = voronoi(x, f, 4, 115)
        if d2 - d1 < 0.6:
            return verdes[0]
        c = verdes[1 + int(ruido(int(x // 4), int(f // 4), 117) * 3)]
        if ruido(x, f, 119) > 0.975:
            c = flores[int(ruido(x, f, 120) * 4)]
        return c
    manta(l, follaje, lambda x: 14 + [0, 1, 2, 3, 2, 1][x % 6], ribete=None, oscurecer_borde=False)
    correas(l, [h("#3d3218"), h("#5a4a24"), h("#776233")], PLATA)
    antiparras(l, [h("#3d3218"), h("#5a4a24"), h("#776233")], [h("#cfeccc"), h("#f4fff2")],
               [h("#3d3218"), h("#5a4a24")])
    return l


def elegante():
    """Rojo: caballero elegante, terciopelo con botones dorados, flecos y corbata de humita."""
    l = Lienzo()
    roj = [h("#5c0f15"), h("#8a1a22"), h("#b0262f"), h("#d1414a")]

    def capitone(i, j):
        if (i + j) % 8 == 0 and (i - j) % 8 == 0:
            return h("#f0cc55")
        if (i + j) % 8 == 0 or (i - j) % 8 == 0:
            return roj[1]
        return roj[3] if ((i + j) % 8 in (1, 2) and (i - j) % 8 in (1, 2, 3)) else roj[2]
    silla(l, roj, costura=None, relleno=capitone)

    def terciopelo(x, f, n):
        return mezcla(h("#c0303a"), h("#7e161e"), f / n * 0.8 + (0.1 if x % 3 == 0 else 0))
    puntas = lambda x: 14 + [0, 1, 2, 3, 3, 2, 1, 0][x % 8]
    alto = manta(l, terciopelo, puntas, ribete=[h("#f0cc55"), h("#b8902f")])
    for x in range(T):                                # flecos dorados en cada punta
        if x in alto and x % 8 in (3, 4):
            l.pon(x, MANTA_Y + alto[x], h("#f0cc55"))
            l.pon(x, MANTA_Y + alto[x] + 1, h("#b8902f"))
    l.dibujo(42, 60, [                                # humita bajo la sonrisa del ghast
        "kk.......kk",
        "kgkk...kkgk",
        "kggkknkkggk",
        "kgkk...kkgk",
    ], {"k": h("#151515"), "g": h("#3a3a3a"), "n": h("#2a2a2a")})
    correas(l, [h("#141414"), h("#262626"), h("#3a3a3a")], ORO)
    antiparras(l, [h("#8e6512"), h("#d4a83a"), h("#f2cf55")], [h("#e6f2f5"), h("#ffffff")],
               [h("#141414"), h("#262626")])
    return l


def dragon():
    """Negro: dragon del End, con escamas, puas en el lomo y ojos morados."""
    l = Lienzo()
    neg = [h("#0d0b10"), h("#18141d"), h("#241e2b"), h("#352b40")]

    def escamas(i, j):
        if 13 <= i <= 18:                             # puas por el medio del lomo
            k = (j - 2) % 6
            mitad = [0, 1, 2, 2, 1, 0][k]
            if abs(i - 15.5) <= mitad + 0.5:
                return h("#6d6577") if i <= 15 else h("#4a4452")
        fila = j // 3
        c = (i + (fila % 2) * 2) % 4
        if j % 3 == 2 or c == 0:
            return neg[0]
        return h("#3b2a4f") if ruido(i // 4, fila, 121) > 0.8 else neg[2]
    silla(l, neg, relleno=escamas)

    def manto(x, f, n):
        fila = f // 3
        c = (x + (fila % 2) * 2) % 4
        if f % 3 == 2 or c == 0:
            return h("#0d0b10")
        return h("#3b2a4f") if ruido(x // 4, fila, 123) > 0.82 else h("#2a2333")
    puntas = lambda x: 13 + [0, 1, 2, 3, 4, 2][x % 6]
    manta(l, manto, puntas, ribete=None)
    en_espalda(l, 40, [
        "pp............pp",
        ".pPp........pPp.",
    ], {"p": h("#b65cff"), "P": h("#f0c0ff")})
    correas(l, [h("#0d0b10"), h("#1f1a26"), h("#33283f")], [h("#3a3046"), h("#8a7aa0")])
    antiparras(l, [h("#0d0b10"), h("#241e2b"), h("#3a3046")], [h("#b65cff"), h("#efd0ff")],
               [h("#0d0b10"), h("#1f1a26")])
    return l


TEMAS = {
    "white": lana, "orange": calabaza, "magenta": shulker, "light_blue": allay,
    "yellow": abeja, "lime": tortuga, "pink": ajolote, "gray": minero,
    "light_gray": rana, "cyan": warden, "purple": enderman, "blue": noche,
    "brown": creaking, "green": hojas, "red": elegante, "black": dragon,
}


# ---------------- globos: un happy ghast con etiqueta ----------------
# Idea de Actions & Stuff (Creeper/Enderman/Pig/Pumpkin Balloon); el dibujo es nuestro.
# Van sobre el happy ghast de Fresh Animations (textura de 128x128, la misma caja de 16x16x16
# desplegada igual que el arnes). Sus caritas son planos aparte que aqui quedan transparentes:
# la cara del globo va pintada en el frente del cuerpo.
# Fresh Animations no usa la caja de adentro, asi que ahi caben la canasta y las cuerdas
# (en el formato de 64: canasta en (0, 48), cuerdas en (40, 48)).
CUERPO = {"arriba": (32, 0), "abajo": (64, 0), "der": (0, 32), "frente": (32, 32),
          "izq": (64, 32), "espalda": (96, 32)}


def _globo(piel, cara):
    l = Lienzo()
    for k, (nombre, (x0, y0)) in enumerate(CUERPO.items()):
        for j in range(32):
            for i in range(32):
                l.pon(x0 + i, y0 + j, piel(nombre, i, j, k))
    cara(l, 32, 32)
    cesta(l)
    return l


def _bloque(paleta, i, j, s, tam=4):
    return paleta[int(ruido(i // tam, j // tam, s) * len(paleta))]


def _patron(l, x0, y0, filas, paleta, escala=4):
    for j, fila in enumerate(filas):
        for i, ch in enumerate(fila):
            if ch in paleta:
                for a in range(escala):
                    for b in range(escala):
                        c = paleta[ch]
                        if isinstance(c, list):
                            c = c[int(ruido(x0 + i * escala + b, y0 + j * escala + a, 5) * len(c))]
                        l.pon(x0 + i * escala + b, y0 + j * escala + a, c)


def cesta(l):
    mimbre = [h("#8a5a2b"), h("#6e4520"), h("#a06c36")]
    for y in range(96, 122):                          # canasta 8x5x8
        for x in range(0, 64):
            if 16 <= x < 32 and y < 112:
                c = h("#3a2410")                      # adentro (se ve desde arriba)
            elif y < 112 and not (32 <= x < 48):
                continue
            elif y in (112, 113):
                c = mimbre[2] if y == 112 else mimbre[1]
            else:
                c = mimbre[0] if ((x // 2) + (y // 2)) % 2 else mimbre[1]
            l.pon(x, y, c)
    for y in range(96, 106):                          # cuerdas 1x4x1
        for x in range(80, 88):
            l.pon(x, y, h("#d8c79a") if (x + y) % 3 else h("#b09c6a"))


def globo_creeper():
    verdes = [h("#5db44a"), h("#4f9b3f"), h("#76c75f"), h("#3f8233"), h("#93d47b")]

    def piel(n, i, j, k):
        return _bloque(verdes, i, j, 200 + k)

    def cara(l, x0, y0):
        negro = [h("#0d0d0d"), h("#1b1b1b"), h("#141414")]
        _patron(l, x0, y0, [
            "........",
            ".XX..XX.",
            ".XX..XX.",
            "...XX...",
            "..XXXX..",
            "..XXXX..",
            "..X..X..",
            "........",
        ], {"X": negro})
    return _globo(piel, cara)


def globo_enderman():
    negros = [h("#161616"), h("#0f0f0f"), h("#1d1d1d"), h("#242424")]

    def piel(n, i, j, k):
        if ruido(i, j, 300 + k) > 0.985:
            return h("#cc00fa")
        return _bloque(negros, i, j, 310 + k)

    def cara(l, x0, y0):
        _patron(l, x0, y0 + 16, ["pPp..pPp"], {"p": h("#cc00fa"), "P": h("#e079fa")})
    return _globo(piel, cara)


def globo_cerdo():
    rosas = [h("#f0a5a2"), h("#e8918f"), h("#f5b7b4"), h("#ec9c99")]

    def piel(n, i, j, k):
        return _bloque(rosas, i, j, 400 + k)

    def cara(l, x0, y0):
        _patron(l, x0, y0, [
            "........",
            "........",
            "........",
            ".WK..KW.",
            "..SSSS..",
            "..NSSN..",
            "..SSSS..",
            "........",
        ], {"W": h("#f4f4f4"), "K": h("#1a1a1a"), "S": h("#f7c1bd"), "N": h("#8f4c4b")})
    return _globo(piel, cara)


def globo_calabaza():
    tonos = [h("#a8480b"), h("#c8600f"), h("#e57d1a"), h("#f39a33")]

    def piel(n, i, j, k):
        if n == "arriba":
            if 13 <= i <= 18 and 13 <= j <= 18:
                return h("#4d5a22") if (i + j) % 3 else h("#6f7f30")
            a = math.atan2(j - 15.5, i - 15.5)
            return tonos[1] if (a / (2 * math.pi) * 10) % 1 < 0.14 else tonos[3]
        if n == "abajo":
            return tonos[1]
        return tonos[[0, 1, 2, 3, 3, 2, 1, 0][i % 8]]       # costillas de la calabaza

    def cara(l, x0, y0):
        _patron(l, x0, y0 + 6, [
            "...k........k...",
            "..kyk......kyk..",
            ".kyyyk....kyyyk.",
            "kkkkkkk..kkkkkkk",
            "................",
            "kk............kk",
            "kykk.kkkkkk.kkyk",
            "kyyykyyyyyykyyyk",
            ".kyyyyykkyyyyyk.",
            "..kkkkk..kkkkk..",
        ], {"k": h("#3a1906"), "y": h("#ffc93d")}, escala=2)
    return _globo(piel, cara)


GLOBOS = [  # (textura, nombres que la activan)
    (globo_creeper, "creeper balloon|globo creeper"),
    (globo_enderman, "enderman balloon|globo enderman"),
    (globo_cerdo, "pig balloon|globo cerdo|globo chancho"),
    (globo_calabaza, "pumpkin balloon|globo calabaza|globo zapallo"),
]


def chico(l):
    """El globo para la cria (ghastling): la misma textura a la mitad (64x64) y un hilo."""
    p = [[l.p[y * 2][x * 2] for x in range(64)] for y in range(64)]
    for y in range(48, 59):                           # hilo 1x10x1 en (40, 48)
        for x in range(40, 44):
            p[y][x] = h("#ececec") if (x + y) % 2 else h("#c9c9c9")
    return p
