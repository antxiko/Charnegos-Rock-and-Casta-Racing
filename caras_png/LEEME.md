# Caras editables de Rock n Roll Racing (Mega Drive, Europe)

**15 retratos de 64x64 píxeles**, en PNG indexados con sus paletas originales.
Abre `TODAS_LAS_CARAS.png` para identificarlos. Esa imagen es una vista ampliada;
edita los PNG individuales numerados del 01 al 15.

Incluye Snake Sanders, Cyberhawk, Ivanzypher, Katarina Lyons, Jake Badlands,
Tarquinn, Olaf, Viper Mackay, Grinder X19, Ragewortt, Roadkill Kelly,
Butcher Icebone, J.B. Slash, Rip y Shred.

## Para editar

- Mantén 64x64, modo indexado y el orden de los 16 colores.
- El índice 0 es transparente. Algunos otros índices son negros y opacos:
  no conviertas todos los píxeles negros en transparencia.
- No uses suavizado ni escalado al guardar el original editable.
- Cada PNG lleva su paleta. En `paletas` tienes además `.gpl`, muestrario PNG
  con índices y `.bin` con las palabras de color nativas de Mega Drive.
- Rip y Shred comparten gráficos, con paletas diferentes. Editar su bloque
  común en una futura reinserción cambiaría ambos retratos.

## Validación

Se cargó `partidas/segundaCarreraParticipantesHeGanado.State` en una instancia
separada de BizHawk 2.11.1. `captura/pantalla.png` muestra la pantalla obtenida
un fotograma después de cargar. El savestate y la ROM originales no se modificaron.

Snake Sanders, Viper Mackay y Rip coinciden exactamente con los gráficos de
VRAM y las paletas de CRAM. Se comprobó también la tabla de sprites: cuatro
piezas de 32x32 en una imagen de 64x64. Los otros retratos se extrajeron de la
ROM y se revisaron en la vista general; no se visualizaron dentro del juego.

Los **15 PNG se releen y reconstruyen sus 2.048 bytes nativos sin diferencias**.
Las paletas conservan las 16 palabras originales; el RGB del PNG usa expansión
lineal de 3 bits a 8 bits. Un filtro de vídeo del emulador puede alterar el RGB mostrado.

No se ha reinsertado ningún dibujo modificado. Estos recursos están comprimidos;
una futura reinserción requiere recomprimir y gestionar el tamaño del bloque.

## Datos y reproducción

`manifest.json` registra nombres, IDs de recursos, offsets y validación individual.
Hay 14 bloques de gráficos distintos, pero 15 combinaciones de dibujo y paleta:

- Seleccionables: recursos gráficos 78–84 y paletas 85–91.
- Rivales: gráficos 92–98 y paletas 99–106.
- Rip: gráfico 98, paleta 105; Shred: gráfico 98, paleta 106. Esta reutilización
  está confirmada por las rutinas de ROM `0x99A8` y `0x9A0A`.
- Compresión LZSS; tabla de recursos en `0x6B000`.

Para regenerar desde la carpeta del proyecto (Python + Pillow):

```powershell
python tools/export_faces.py
```

Usa los volcados de `captura` para repetir las comprobaciones. Para recapturar,
ejecuta `tools/capture_faces.lua` en una instancia de BizHawk con la copia de la
ROM cargada; el script cierra esa instancia al terminar.
