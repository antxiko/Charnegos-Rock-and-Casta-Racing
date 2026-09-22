# Coches de Rock n Roll Racing, Mega Drive (Europe)

Abre **VISTA_GENERAL.png** para elegir coche y color. Cada fila corresponde a
una carpeta `coche_01` a `coche_05`; las columnas son las diez paletas base.

- Cada coche tiene **45 fotogramas almacenados**, de **48 x 48 píxeles**.
  Incluyen distintas orientaciones y poses; no son 45 ángulos uniformes.
- `vista_00.png` a `vista_44.png`: PNG indexados individuales con paleta 00.
- `hoja_paleta_00.png` a `hoja_paleta_09.png`: el mismo coche en diez colores,
  en una cuadrícula de 9 columnas por 5 filas, sin separación. Cada celda mide 48x48.
- `paleta_XX.gpl`: paleta importable en editores compatibles con GIMP Palette.
- `paleta_XX.png`: muestrario con los índices numerados.
- `paleta_XX.bin`: las 16 palabras de color originales de Mega Drive, big endian.
- `manifest.json`: dirección exacta de cada fotograma en la ROM.

## Edición

Conserva el tamaño y el modo indexado. El índice 0 es transparente. No uses
suavizado ni reorganices la paleta. Las hojas son versiones alternativas del mismo
gráfico: elige una para editar. La imagen VISTA_GENERAL es una previsualización
ampliada, no una plantilla para reinsertar.

Los colores se seleccionan durante el juego: no existe una única paleta fija por
modelo. Las diez exportadas son las tablas base reales. El juego comparte líneas
de paleta entre corredores, remapea índices para el segundo coche, modifica colores
en ciertos estados y anima tonos de las ruedas. Estos PNG muestran la base, no todos
los estados de color de una carrera. Cambiar una paleta puede afectar a otros coches.

## Evidencia y reproducción

ROM original intacta: 1.048.576 bytes; SHA-256:
`b65b7de45420e7618fef1b9bef13076389fdf7e0da8dfec1de23f528dcd170cb`.

- Banco de coches sin compresión: `0x0BF500`, paso `0x480` bytes por fotograma.
- Rutina `0x6394`: calcula `0x0BF500 + fotograma * 0x480`.
- Tabla `0x6A9E`: bases 0, 45, 90, 135 y 180 para los cinco modelos.
  El valor siguiente, 225, no se ha exportado como sexto coche.
- Paletas: diez bloques de 32 bytes desde `0x6776`; rutina de selección y
  combinación en `0x5DAC`–`0x5E34`.
- **225/225 PNG individuales releídos y convertidos a bytes nativos idénticos
  a sus bloques originales**. También se comprueba la conversión de las 50 hojas
  mientras se construyen. Hojas y vista general inspeccionadas visualmente.
- Pendiente: reinserción de un dibujo modificado y prueba dentro del emulador.
  La conversión inversa verificada no equivale a una prueba jugable.

Actualización: validado también con BizHawk 2.11.1. Doce sprites de carrera de
los modelos 01, 03, 04 y 05 coinciden exactamente con los datos nativos/remapeados
y con el montaje independiente de la tabla de sprites. Las paletas capturadas y
las imágenes están en `../validation_bizhawk/`. El modelo 02 sigue sin contraste
en ejecución; la reinserción de dibujos nuevos continúa pendiente.

Para regenerar, desde la carpeta del proyecto:

```powershell
python tools/export_cars.py
```

Requiere Python y Pillow. `tools/extract_rnr.py` contiene la investigación separada
del banco comprimido de menús/tienda: sus previews grises son material técnico,
no los coches editables. Tres recursos no se descomprimieron con ese procedimiento.
La referencia inicial del formato LZSS fue
[sega2asm](https://github.com/hansbonini/sega2asm/blob/master/compress/lzss_blizzard.go);
se contrastó con la rutina de esta ROM en `0x0EDC` y la tabla en `0x6B000`.
