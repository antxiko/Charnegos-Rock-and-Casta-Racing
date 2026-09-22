# La entrada triunfal

Ejecuta desde la raiz del proyecto:

```powershell
python tools/export_intro.py
```

El extractor genera PNG indexados con la paleta original:

- `interplay_logo.png` y `blizzard_logo.png`: las dos pantallas de apertura.
- `titulo_fondo_capa_trasera.png`: fondo principal del titulo.
- `titulo_fondo_capa_frontal.png`: adornos superpuestos; el indice 0 es transparente.
- `titulo_letras.png`: las letras animadas, colocadas como quedan al terminar el rebote; el indice 0 es transparente.
- `titulo_fondo.png` y `titulo_completo.png`: referencias montadas. No se reinsertan directamente.
- `tiles/`: despieces para trabajar baldosa por baldosa.
- `paletas/`: paletas en formato GIMP y binario CRAM.

Edita los cinco primeros PNG sin cambiar sus dimensiones ni inventar colores fuera de su paleta. Aseprite y GIMP conservan bien el modo indexado. No reorganices la paleta: cada grupo de 16 colores es una linea distinta de la Mega Drive.

Para fabricar una ROM nueva:

```powershell
python tools/export_intro.py --import-dir intro_png --output-rom roms_editadas/RockAndCasta-intro.md
```

Tambien puedes arrastrar la carpeta de los PNG sobre `APLICAR_INTRO.cmd`. La ROM original nunca se sobrescribe. Si un dibujo nuevo comprime peor de lo que cabe en su hueco original, la herramienta se para y dice que recurso se ha pasado de talla; simplifica un poco el dibujo y vuelve a darle candela.
