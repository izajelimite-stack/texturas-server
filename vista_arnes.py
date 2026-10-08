"""Vista previa de los arneses puestos en el happy ghast (de Fresh Animations), sin abrir el juego.

Uso: python vista_arnes.py [colores o globo_creeper...]  ->  .cache/arnes/vista_<n>.png, de a 4 arneses por imagen.
Cada arnes sale dos veces: de frente y de atras. Las antiparras salen bajadas (como cuando lo montan).
"""
import math, os, sys, zipfile
import generar as g
import arneses as a

C30 = math.cos(math.pi / 6)
SALIDA = os.path.join(g.BASE, ".cache", "arnes")


def ghast():
    g.lobo_fresh_animations()
    z = zipfile.ZipFile(os.path.join(g.BASE, ".cache", "FreshAnimations_v1.10.5.zip"))
    return g.leer_png(z.read("assets/minecraft/textures/entity/ghast/happy_ghast.png"))[2]


def sobre(abajo, arriba):
    return arriba if arriba[3] > 25 else abajo


REGION = {"arriba": (32, 0), "frente": (32, 32), "der": (0, 32), "izq": (64, 32), "espalda": (96, 32)}


def cara(nombre, gh, ar, girar=False):
    x0, y0 = REGION[nombre]

    def m(s, t):
        if girar:
            s, t = 1 - s, 1 - t
        px, py = min(31, int(s * 32)), min(31, int(t * 32))
        c = gh[y0 + py][x0 + px]
        if nombre == "frente" and 1 / 16 <= s < 15 / 16 and 1 / 16 <= t < 15 / 16:
            c = sobre(c, gh[2 + int((t - 1 / 16) * 32)][98 + int((s - 1 / 16) * 32)])
        c = sobre(c, ar[y0 + py][x0 + px])
        if nombre == "frente" and 0 <= py - 7 < 10:
            c = sobre(c, ar[74 + py - 7][10 + px])
        return c
    return m


def vista(caras, E, fondo):
    W, H = int(2 * E * C30) + 4, int(2 * E) + 4
    ox, oy = W / 2, E + 2

    def P(X, Y, Z):
        return ox + (X - Z) * E * C30, oy - Y * E + (X + Z) * E * 0.5
    planos = []
    for (O, U, V, muestra, sombra) in caras:
        o = P(*O)
        u = [P(O[0] + U[0], O[1] + U[1], O[2] + U[2])[k] - o[k] for k in range(2)]
        v = [P(O[0] + V[0], O[1] + V[1], O[2] + V[2])[k] - o[k] for k in range(2)]
        det = u[0] * v[1] - u[1] * v[0]
        planos.append((o, u, v, det, muestra, sombra))
    img = [[fondo] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            for (o, u, v, det, muestra, sombra) in planos:
                dx, dy = x + 0.5 - o[0], y + 0.5 - o[1]
                s = (dx * v[1] - dy * v[0]) / det
                t = (u[0] * dy - u[1] * dx) / det
                if 0 <= s < 1 and 0 <= t < 1:
                    c = muestra(s, t)
                    if c[3] > 25:
                        img[y][x] = g.luz(c, sombra) if hasattr(g, "luz") else a.luz(c, sombra)
                    break
    return img


def dos_vistas(gh, ar, E, fondo):
    frente = [((0, 1, 1), (1, 0, 0), (0, -1, 0), cara("frente", gh, ar), 0.82),
              ((1, 1, 1), (0, 0, -1), (0, -1, 0), cara("izq", gh, ar), 0.62),
              ((0, 1, 0), (1, 0, 0), (0, 0, 1), cara("arriba", gh, ar), 1.0)]
    atras = [((0, 1, 1), (1, 0, 0), (0, -1, 0), cara("espalda", gh, ar), 0.82),
             ((1, 1, 1), (0, 0, -1), (0, -1, 0), cara("der", gh, ar), 0.62),
             ((0, 1, 0), (1, 0, 0), (0, 0, 1), cara("arriba", gh, ar, girar=True), 1.0)]
    return vista(frente, E, fondo), vista(atras, E, fondo)


def main(colores):
    os.makedirs(SALIDA, exist_ok=True)
    gh = ghast()
    fondo = (120, 170, 210, 255)
    E = 150
    for n in range(0, len(colores), 4):
        grupo = colores[n:n + 4]
        columnas = []
        for color in grupo:
            if color.startswith("globo"):             # un globo, sin arnes
                cuerpo = getattr(a, color)().p
                columnas.append(dos_vistas(cuerpo, a.Lienzo().p, E, fondo))
                continue
            ar = a.TEMAS[color]().p
            columnas.append(dos_vistas(gh, ar, E, fondo))
        w, hh = len(columnas[0][0][0]), len(columnas[0][0])
        hoja = [[fondo] * (w * len(columnas)) for _ in range(hh * 2)]
        for k, (va, vb) in enumerate(columnas):
            for y in range(hh):
                hoja[y][k * w:(k + 1) * w] = va[y]
                hoja[hh + y][k * w:(k + 1) * w] = vb[y]
        ruta = os.path.join(SALIDA, f"vista_{n // 4 + 1}.png")
        open(ruta, "wb").write(g.png(len(hoja[0]), len(hoja), hoja))
        print(ruta, " ".join(grupo))


if __name__ == "__main__":
    main(sys.argv[1:] or list(a.TEMAS))
