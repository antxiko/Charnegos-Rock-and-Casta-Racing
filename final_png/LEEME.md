# El final, abierto en canal

Extrae todo con:

```powershell
python tools/export_ending.py
```

La carpeta queda dividida en cuatro escenas:

- `01_hangar`: las dos capas mecánicas desplazables y seis hojas de animación con la nave, el coche y sus efectos.
- `02_planeta`: mapa completo de 512x224, tiles y las fases roja y verde de su paleta animada.
- `03_ciudad`: fondo de 512x256 y capa del primer plano por separado.
- `04_escenario`: escenario y público de la ceremonia final.

Cada escena contiene sus capas como PNG indexados, los tiles originales y las paletas `.gpl` y `.bin`. `montaje_referencia.png` sirve para entender el conjunto y no se reinserta. Algunos mapas miden 512 píxeles porque la cámara recorre la escena; no los recortes a los 256 píxeles visibles en una captura.

En el planeta, `paleta_fase_roja` corresponde al plano rojo mostrado al principio y `paleta_fase_verde` a la transformación posterior. Ambas se capturaron directamente de CRAM en BizHawk. El PNG editable usa la fase roja.

No cambies el tamaño de los PNG ni reorganices sus índices de color. Para crear otra ROM:

```powershell
python tools/export_ending.py --import-dir final_png --output-rom roms_editadas/RockAndCasta-final.md
```

También puedes arrastrar `final_png` sobre `APLICAR_FINAL.cmd`. La herramienta recalcula el checksum y nunca sobrescribe la ROM original. Si un dibujo nuevo no cabe comprimido en el hueco del recurso, se detiene indicando cuál se ha pasado.
