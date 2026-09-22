# Mapa de textos y espacio de la ROM

## Banco original

- Banco principal: `0x00398C-0x004BE9`, 4702 bytes.
- Tabla de 213 referencias: `0x0037CE-0x00398B`.
- Base absoluta usada por el 68000: operando en `0x003664`.
- Cinco cadenas pequeñas del sistema permanecen en `0x000481-0x0004E9` porque las usa el arranque por separado.

Los bloques de ceros encontrados dentro del primer MiB no se consideran huecos libres. Muchos separan recursos comprimidos o son espacio de trabajo reservado por sus tablas; ocuparlos sin reconstruir cada archivo podría romper gráficos, música o circuitos.

## Zona interna reservada

Cuando una traducción supera su hueco original, la herramienta utiliza un bloque vacío que ya existe dentro del cartucho de 1 MiB:

- Hueco vacío comprobado: `0x064E11-0x06AFFF`, 25071 bytes.
- Zona usada por seguridad: `0x065000-0x06AFFF`, 24576 bytes.
- La tabla de recursos comienza justo después, en `0x06B000`, y nunca se toca.

El importador verifica primero que toda la zona siga llena de ceros, reconstruye el banco, actualiza las 213 referencias, cambia la base del código 68000 y recalcula el checksum. La ROM conserva exactamente su tamaño original de 1 MiB. Si los textos superan 24576 bytes, la herramienta se detiene.

## Segundo hueco confirmado

- Dirección: `0x015A7B-0x018FFF`.
- Tamaño: 13701 bytes.
- Uso actual: ninguno; reservado para futuras ampliaciones sin aumentar la ROM.
- Límite posterior: el driver Z80 Sound Images comienza en `0x019000`.

La zona es completamente cero en la ROM original. El desensamblado no encontró saltos, llamadas ni referencias 68000 hacia su interior. Para validarla se creó una ROM temporal rellenando los 13701 bytes con el patrón alterno `5A/A5`. Tras actualizar el checksum, cinco puntos de la cinemática final y cuatro estados distintos de carrera produjeron capturas idénticas a la ROM original en BizHawk. Esta prueba confirma el uso observado en emulación; no sustituye una futura prueba completa en cartucho físico.

## Fuente castellana

Las fuentes comprimidas son los recursos 0 y 1. Se reutilizan seis posiciones ASCII que el juego original no emplea:

| Carácter | Byte interno | Casilla sustituida |
|---|---:|---|
| Ñ / ñ | `0x40` | `@` |
| Á / á | `0x5B` | `[` |
| É / é | `0x5C` | `\` |
| Í / í | `0x5D` | `]` |
| Ó / ó | `0x5E` | `^` |
| Ú / ú | `0x5F` | `_` |

El JSON continúa siendo UTF-8. El importador convierte esos caracteres a sus bytes internos y modifica ambos recursos de fuente automáticamente.
