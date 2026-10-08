# texturas-server

Paquete de texturas de un server privado de Minecraft (Java, 26.2). El server lo manda solo al
entrar; no hace falta descargarlo.

Trae los fondos de los menus propios del server (se dibujan como una letra de la fuente
`amigos:menus` en el titulo del menu, sin mods).

`python3 generar.py <version>` arma `dist/texturas-v<version>.zip`. Cada version es un archivo
nuevo, asi el link cambia y nadie se queda con una copia vieja.

Tambien trae cosas del happy ghast, con dibujo propio (`arneses.py`; ideas de Actions & Stuff):
un diseno distinto para cada color de arnes, globos por nombre ("Globo creeper", "Globo cerdo",
"Globo enderman", "Globo calabaza") y "Sin arnes" para que no se vea el arnes.
`python vista_arnes.py` dibuja una vista previa en `.cache/arnes/` sin abrir el juego.
