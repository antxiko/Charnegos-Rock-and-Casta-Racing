# El final, abierto en canal

Extrae todo con:

```powershell
python tools/export_ending.py
```

La carpeta queda dividida en cuatro escenas:

- `01_hangar`: las dos capas mecánicas desplazables y seis hojas de animación con la nave, el coche y sus efectos.
- `02_planeta`: mapa completo de 512x224, tiles y las fases roja y verde de su paleta animada.
- `03_ciudad`: fondo de 512x256 y capa del primer plano por separado.
- `04_escenario`: escenario y público de la ceremonia final en capas separadas. Incluye 28 bloques de personaje de 24x24, el presentador montado como referencia, los tiles de la carrera de exhibición y sus datos de secuencia.

Cada escena contiene sus capas como PNG indexados, los tiles originales y las paletas `.gpl` y `.bin`. `montaje_referencia.png` sirve para entender el conjunto y no se reinserta. Algunos mapas miden 512 píxeles porque la cámara recorre la escena; no los recortes a los 256 píxeles visibles en una captura.

En el planeta, `paleta_fase_roja` corresponde al plano rojo mostrado al principio y `paleta_fase_verde` a la transformación posterior. Ambas se capturaron directamente de CRAM en BizHawk. El PNG editable usa la fase roja.

En el escenario, `capa_01_mapa_209.png` contiene el escenario y `capa_02_mapa_211.png` el público delantero. Ambos mapas miden 32x64 tiles (256x512 píxeles) y conservan la zona vertical que recorre la cámara. Los PNG de `sprites_24x24` son las piezas editables del recurso 212; los cuatro últimos forman `presentador_montado.png`. `paletas_personajes` separa las siete paletas del recurso 213. Los ficheros `datos_secuencia_215.bin` a `220.bin` gobiernan las seis variantes de la carrera de exhibición y se conservan aparte para estudiarlas sin confundirlas con gráficos.

No cambies el tamaño de los PNG ni reorganices sus índices de color. Para crear otra ROM:

```powershell
python tools/export_ending.py --import-dir final_png --output-rom roms_editadas/RockAndCasta-final.md
```

También puedes arrastrar `final_png` sobre `APLICAR_FINAL.cmd`. La herramienta recalcula el checksum y nunca sobrescribe la ROM original. Si un dibujo nuevo no cabe comprimido en el hueco del recurso, se detiene indicando cuál se ha pasado.
