# Todos los circuitos, editables

**Abre `EDITOR.html` en el navegador.** Incluye los **72 diseños de circuito**
presentes en la ROM y los **6 mundos**. El campeonato repite algunos diseños:
no son 72 bancos gráficos distintos ni 72 carreras consecutivas.

## Editar el montaje del mapa

1. Elige mundo y circuito, o pulsa su miniatura.
2. En **Seleccionar tile**, pulsa una zona del mapa. Verás su número, paleta,
   capa y todas sus apariciones; queda seleccionado como pincel.
3. Elige la capa de destino —carretera o decorados— y pulsa **Pintar montaje**.
   Pulsa o arrastra para sustituir tiles. Puedes ajustar paleta, volteos y prioridad.
4. **Deshacer** revierte cambios. **Guardar edición JSON** descarga tu proyecto.
5. Para recuperarlo, elige el mismo circuito y pulsa **Abrir edición JSON**.

Guarda antes de cambiar de circuito. El editor avisa si quedan cambios sin guardar.
Funciona localmente: no necesita servidor ni conexión. El JSON conserva el montaje
de ambas capas con todos sus atributos, no solo una captura de pantalla.

## Editar los píxeles

Pulsa **PNG indexado del tile** para localizar la imagen original de **8x8**.
Los PNG están en `bancos/XX/tiles/paleta_N`. Edítalos con un editor de píxeles,
conservando modo indexado, tamaño y orden de los 16 colores. Índice 0 transparente.

Hay **8.302 PNG**, contando las variantes de paleta. El mismo número de tile con
distintas paletas corresponde a los mismos datos gráficos: no son dibujos
independientes. Cambiar el dibujo original afecta a todos sus usos y a otros
circuitos que comparten el banco.

El editor web pinta el montaje; no modifica ni recarga automáticamente los PNG
de tiles. El atlas numerado permite localizar también tiles no usados en el mapa
seleccionado. Para esos tiles, la paleta 3 es una vista de referencia.

## También puedes editar en Tiled

Cada carpeta `mapas/NN` contiene **`mapa_editable.tmx`**, con tilesets y paletas
enlazados a `bancos`. Ábrelo desde esa carpeta para mantener las rutas relativas.
Separa las dos capas en prioridad baja y alta, conservando el orden de dibujo
de Mega Drive. Puedes colocar tiles, reflejarlos y editar el montaje.

Los tilesets PNG usados por Tiled son atlas RGBA de referencia; los tiles
individuales indexados son la fuente adecuada para retocar gráficos nativos.

Formato contrastado con la documentación oficial:
[TMX](https://doc.mapeditor.org/en/stable/reference/tmx-map-format/) y
[identificadores y volteos](https://doc.mapeditor.org/en/stable/reference/global-tile-ids/).

## Qué hay en cada carpeta

- `mapas/01` a `mapas/72`: circuito completo PNG, dos capas transparentes,
  miniatura, mapa editable TMX y datos del visor.
- `definicion_original.bin`: los 1.236 bytes de definición lógica de ese circuito,
  extraídos sin cambiar. No es una imagen ni un mapa de tiles plano.
- `mapas_generados.bin`: dos capas completas, palabras big endian, 384x115 tiles
  por capa; tamaño del lienzo: **3072x920 píxeles**, incluidos los bordes del búfer.
- `bancos/00` a `bancos/05`: tiles indexados, paletas GPL/BIN, atlas y tilesets TSX.
- `SEIS_MUNDOS.png`: una vista de ejemplo de cada mundo.
- `manifest.json`: catálogo, IDs de recursos, offsets y recuentos.

| Banco | Mundo | Tiles gráficos | Comienzo en ROM |
|---|---|---:|---|
| 00 | CHEM VI | 830 | `0x898C8` |
| 01 | DRAKONIS | 823 | `0x95292` |
| 02 | BOGMIRE | 977 | `0x83D16` |
| 03 | NEW MOJAVE | 966 | `0xA1094` |
| 04 | NHO | 917 | `0x8EAB6` |
| 05 | INFERNO | 906 | `0x9AD08` |

Se incluyen además los tiles auxiliares de objetos que aparecen en el montaje.

## Alcance de la edición

**Los proyectos editados todavía no se reinsertan en la ROM.** El motor genera
el mapa visual desde una definición lógica, alturas y rutinas de decoración.
Mover tiles en el visor o en Tiled no actualiza colisiones, alturas, recorrido de
la IA o progreso de carrera. No lo presentes como un circuito jugable modificado.

Para cambiar el aspecto conservando el trazado, el siguiente paso sería reinsertar
los tiles editados en su banco comprimido. Un editor de trazados jugables requiere
además modificar la definición lógica y validar las reglas del motor.

Los fondos incluyen decoración pseudoaleatoria. Aquí se usa una semilla reproducible
procedente de la RAM capturada; la posición de algunos objetos puede diferir al
volver a entrar en una carrera. Paletas y objetos dinámicos son una instantánea,
no todas las fases de animación. Coches y HUD no forman parte de estos mapas.

## Validación realizada

- Los 72 recursos de circuito (107–178) están extraídos. Su asociación a mundos
  procede de las tablas reales de campeonato de la ROM, no de una suposición.
- Se ejecuta el constructor 68000 original `0x1A400` con Unicorn/M68000 y su
  conversión de diccionario `0xA14C`; todos los constructores terminaron.
- El circuito de tu partida es el **ID 37, CHEM VI**. Su carretera regenerada
  coincide con la reconstrucción de BizHawk en **44.160/44.160 referencias**.
  La decoración del fondo varía con la semilla, como se indica arriba.
- Los **72 TMX** vuelven a convertirse en las dos capas nativas sin diferencias.
- Los 8.302 PNG se releen y conservan exactamente sus índices de píxel originales.
- Editor comprobado en Edge: selección entre mundos, pintar una posición,
  deshacer, guardar y restaurar el JSON sin diferencias, capas y cuadrícula.
  Evidencia en `verificacion`. Esa edición de prueba no modifica ningún original.
- Se revisó visualmente un mapa de cada mundo. No se han jugado los 72 circuitos
  en BizHawk ni probado una ROM con cambios.

La ROM y las partidas originales permanecen intactas.

Para regenerar la extracción: `python tools/export_all_tracks.py` desde el proyecto.
Requiere Python, Pillow, NumPy y Unicorn, además del volcado existente
`circuitos_png/captura/RAM.bin`. El editor entregado no requiere Python.
