# Circuito y decorados editables

**Empieza abriendo `EXPLORAR.html` con tu navegador.** No necesita servidor.
Muestra el circuito completo de la partida suministrada: **3072x920 píxeles**.

1. Elige carretera, decorados o ambas capas. Puedes ampliar y mostrar la cuadrícula.
2. Pulsa cualquier punto. El panel muestra el número de tile, su paleta, sus
   volteos, prioridad y la pieza de 32x8 a la que pertenece.
3. Se resaltan todas las apariciones del mismo tile. Abre su PNG desde el panel.
4. Edita ese PNG en un editor de píxeles manteniendo **8x8, modo indexado y
   los mismos 16 índices de paleta**. Guarda tus cambios en una copia aparte.

El visor sirve para localizar y entender las piezas; no es un editor de dibujo
ni reimporta cambios. Los PNG individuales son los originales editables.

## Archivos útiles

- `CIRCUITO_COMPLETO.png`: reconstrucción a tamaño nativo, sin coches ni HUD.
- `capa_0.png`: carretera y elementos del plano delantero, con transparencia.
- `capa_1.png`: terreno y decorados del plano trasero, con transparencia.
- `ATLAS_TILES_NUMERADOS.png`: los 830 tiles del banco, ampliados y numerados.
- `tiles/paleta_N/tile_XXXX.png`: tiles individuales indexados. El número es su
  índice en VRAM; se conserva en mapas, atlas y visor.
- `paletas/paleta_N.gpl`: las paletas de la partida para importar en el editor.
  Los `.bin` contienen los colores nativos de Mega Drive.
- `ATLAS_PIEZAS_NUMERADAS.png` y `piezas_32x8`: referencias visuales del montaje.
  Son cuatro tiles consecutivos horizontalmente, con paleta y volteos aplicados.
  Estas vistas RGBA ayudan a entender las piezas; edita los tiles indexados.
- `mapa_capa_0.csv` y `mapa_capa_1.csv`: cada posición del mapa, tile, paleta,
  volteos, prioridad y referencia de pieza. Las coordenadas están en tiles de 8x8.
- `manifest.json`: procedencia en ROM, recursos, piezas y verificaciones.
- `captura/pantalla.png`: captura de BizHawk de tu partida.

## Cómo lo monta el juego

La jerarquía que hemos reconstruido es:

**píxeles -> tile de 8x8 -> pieza horizontal de 32x8 -> dos capas de mapa**.

Cada pieza referencia cuatro tiles. Cada referencia puede elegir una de las
cuatro paletas, voltear horizontal/verticalmente y marcar prioridad. No hace
falta dibujar otra copia de un tile para reflejarlo.

Los mapas capturados tienen **96x115 piezas**, equivalentes a **384x115 tiles**.
La carretera y el terreno son capas diferentes. El PNG combinado respeta la
transparencia y la prioridad de ambas. Es la extensión del búfer de mapa
reconstruido, incluidos sus bordes, no un mosaico de capturas de pantalla.

Los tramos grandes y decorados completos se construyen con muchas piezas.
El juego genera este montaje a partir de la definición lógica del circuito,
sus alturas y rutinas de decoración; no guarda este PNG plano en la ROM.

## Qué puedes cambiar y qué afecta

- Cambiar los píxeles de un tile modifica **todas sus apariciones** y los otros
  circuitos que compartan ese banco de gráficos.
- Algunas imágenes del mismo número aparecen bajo paletas distintas: son los
  mismos bytes de gráficos vistos con otros colores, no gráficos independientes.
- El índice 0 de cada paleta es transparente; otros índices negros son opacos.
- Se exportan **877 PNG de tiles**: los 830 originales con paleta 3, variantes
  de paleta utilizadas en el circuito y los tiles auxiliares que aparecen en él.
  Para un tile sin uso en este circuito, la paleta 3 es una vista de referencia,
  no una asignación universal para todos los circuitos.
- Hay **485 piezas de diccionario de ROM** y **15 piezas dinámicas de RAM**.
  Las dinámicas se identifican por referencias con bit `0x4000` (por ejemplo
  `4000`). Algunas muestran objetos o estados que cambian durante la carrera.
- Las paletas y piezas dinámicas representan el instante de esta partida.
  Los colores animados pueden variar al avanzar la carrera.
- Esto prepara gráficos editables y documenta su montaje. **No se ha creado un
  importador ni una ROM modificada**. Cambiar el trazado en estos CSV no cambia
  colisiones, alturas, ruta de la IA ni el circuito lógico del juego.

## Ubicación y comprobaciones

Para la ROM europea con SHA-256
`b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb`:

- Banco de gráficos cargado: **recurso 60, ROM `0x898C8`**, comprimido LZSS.
  Produce 26.560 bytes / 830 tiles, cargados desde VRAM `0x0020`.
- Diccionario de piezas: **recurso 59, ROM `0x889A0`**, registros de 8 bytes
  sin compresión. No confundirlos con los previews genéricos del primer análisis.
- Tiles auxiliares: recurso 189, cargado desde VRAM `0x7EE0` (tile 1015).
- Capas generadas en RAM: `0xFF0458` y `0xFF5A98`, 22.080 bytes cada una.
- Diccionario dinámico: RAM `0xFFB0D8`.
- Rutina de construcción del circuito: ROM `0x1A400`; consulta y transmisión
  de las piezas a VRAM: `0xA278` y siguientes.

**Verificado:** los 830 tiles descomprimidos son idénticos al banco completo
en VRAM. Todos los PNG individuales reconstruyen exactamente sus bytes nativos.
La ventana visible de 32x28 tiles coincide con el mapa completo: **896/896
referencias en cada capa**, con origen (268,54) en coordenadas de tile.
Se ha inspeccionado visualmente el mapa completo reconstruido.

La partida original `partidas/SegundoCircuitoHeGanada8de8.State` y la ROM no
se modificaron. No se ha probado aún ningún gráfico modificado dentro del juego.

Regenerar (Python, Pillow y NumPy), desde la carpeta del proyecto:

```powershell
python tools/export_track.py
```

Los volcados necesarios están en `captura`. `tools/capture_track.lua` permite
repetir la captura en una instancia dedicada de BizHawk, que cierra al finalizar.
