# Charnego's Rock & Casta Racing

Herramientas de investigación y modificación para la versión europea de **Rock 'n' Roll Racing de Mega Drive**.

El proyecto permite extraer, editar y reinsertar:

- coches y sus paletas;
- retratos de los participantes;
- samples de voz PCM;
- tiles, decorados y mapas de los 72 circuitos;
- las seis músicas del driver Sound Images v1.20;
- las 214 cadenas de interfaz, diálogos, finales y créditos;
- MIDI y secuencias nativas editables;
- capturas VGM y proyectos para Furnace Tracker.

## Requisitos

- Windows o un sistema con Python 3.10 o posterior;
- una ROM europea obtenida legalmente por el usuario, llamada `Rock 'n' Roll Racing (Europe).md`;
- dependencias de `requirements.txt`;
- BizHawk para las comprobaciones opcionales dentro del juego;
- Furnace Tracker para abrir los proyectos `.fur` generados.

```powershell
python -m pip install -r requirements.txt
python tools/export_cars.py
python tools/export_faces.py
python tools/export_samples.py
python tools/export_all_tracks.py
python tools/export_music.py --export
python tools/export_texts.py
```

Para generar VGM y módulos Furnace se necesita también [vgm2fur](https://github.com/std282/vgm2fur):

```powershell
python -m pip install "git+https://github.com/std282/vgm2fur.git"
python tools/export_music_vgm.py
python tools/convert_vgm_to_furnace.py
```

Los programas verifican el SHA-256 de la ROM europea conocida y generan copias nuevas al reinsertar cambios. No deben sobrescribir la ROM original.

## Contenido del repositorio

El repositorio publica código y documentación propia. No incluye ROMs, savestates, gráficos, audio, música ni otros datos extraídos del juego. Cada usuario debe generar esos recursos localmente desde su propia copia.

Los scripts Lua de `tools/` documentan las validaciones realizadas con BizHawk. Algunas rutas y nombres de savestate corresponden al entorno de investigación original y deben adaptarse para repetirlas.

## Estado

Las extracciones principales tienen comprobación binaria de ida y vuelta. Las modificaciones de música se han probado cargando sus bloques en la RAM Z80 de BizHawk. La conversión Furnace es útil para edición y análisis; la reinserción automática de un `.fur` arbitrario aún no está implementada. Para reinsertar música se usa el importador MIDI o el editor de secuencias nativas generado por `export_music.py`.

## Aviso

Proyecto comunitario y no oficial, sin relación con Blizzard Entertainment, Interplay, Electronic Arts ni los propietarios de las músicas originales. **Rock 'n' Roll Racing** y sus recursos pertenecen a sus respectivos titulares.
