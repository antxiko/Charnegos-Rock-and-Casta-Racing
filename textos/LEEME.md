# Textos editables

`textos.json` contiene **214 cadenas** de la ROM europea: interfaz, pilotos, planetas, menús, tienda, equipamiento, contraseña, rivales, resultados, final, créditos y avisos del sistema.

## Editar

1. Abre `EDITOR.html`.
2. Selecciona `textos.json`.
3. Edita y descarga `textos_editados.json`.
4. Arrastra el JSON descargado sobre `APLICAR_TEXTOS.cmd`.
5. Encontrarás una ROM nueva dentro de `../roms_editadas/`.

También puedes editar directamente `textos.json` con cualquier editor de texto. Modifica únicamente el campo `text`. Los campos `id`, `offset`, `max_bytes`, `line_widths` y `original_hex` protegen la estructura de la ROM y el importador comprueba que no hayan cambiado.

## Límites

- Conserva el número de líneas de cada cadena.
- Cada línea debe caber en el ancho indicado por `line_widths`.
- Usa caracteres ASCII. La fuente original no dispone directamente de `Ñ` ni vocales acentuadas; usa `N` y vocales sin tilde.
- Los saltos de línea del JSON se convierten al byte `0x0D` usado por el juego.
- Una traducción más corta se rellena internamente con ceros sin mover las cadenas siguientes.

La herramienta mantiene todas las direcciones originales. De esta forma también funcionan las cadenas accedidas mediante desplazamientos o tablas no relocables. Si una traducción no cabe, hay que abreviarla; la recolocación de todo el banco requeriría modificar referencias dentro del código 68000.

## Comprobaciones

- Exportar y reinsertar las 214 cadenas sin cambios produce una ROM idéntica byte a byte.
- Al modificar textos, se actualiza el checksum del encabezado de Mega Drive.
- La ROM original nunca se sobrescribe y el archivo de salida debe ser nuevo.
