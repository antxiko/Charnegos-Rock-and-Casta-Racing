# Textos editables

`textos.json` contiene **214 cadenas** de la ROM europea: interfaz, pilotos, planetas, menús, tienda, equipamiento, contraseña, rivales, resultados, final, créditos y avisos del sistema.

## Editar

1. Abre `EDITOR.html`.
2. Selecciona `textos.json`.
3. Edita y descarga `textos_editados.json`.
4. Arrastra el JSON descargado sobre `APLICAR_TEXTOS.cmd`.
5. Encontrarás una ROM nueva dentro de `../roms_editadas/`.

También puedes editar directamente `textos.json` con cualquier editor de texto. Modifica únicamente el campo `text`. Los campos `id`, `offset`, `max_bytes`, `line_widths` y `original_hex` protegen la estructura de la ROM y el importador comprueba que no hayan cambiado.

## Límites y recolocación

- Conserva el número de líneas de cada cadena.
- Cada línea debe caber en el ancho indicado por `max_line_chars`. Ese límite pertenece a la pantalla, no al antiguo hueco de la cadena.
- Se admiten `Ñ`, `ñ`, `Á`, `á`, `É`, `é`, `Í`, `í`, `Ó`, `ó`, `Ú` y `ú`. La fuente se amplía automáticamente al usarlos.
- Los saltos de línea del JSON se convierten al byte `0x0D` usado por el juego.
- Si todo cabe, la ROM conserva sus direcciones originales. Si una cadena crece, el banco completo se recoloca en un hueco interno de 24576 bytes. La ROM permanece siempre en 1 MiB.

La distribución, los punteros y la zona ampliada están documentados en `MAPA_ROM.md`.

## Comprobaciones

- Exportar y reinsertar las 214 cadenas sin cambios produce una ROM idéntica byte a byte.
- Al modificar textos, se actualiza el checksum del encabezado de Mega Drive.
- Una prueba en BizHawk confirmó el banco recolocado y la `Ñ` dibujada por la fuente nueva.
- La ROM original nunca se sobrescribe y el archivo de salida debe ser nuevo.
