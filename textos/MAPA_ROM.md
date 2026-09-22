# Mapa de textos y espacio de la ROM

## Banco original

- Banco principal: `0x00398C-0x004BE9`, 4702 bytes.
- Tabla de 213 referencias: `0x0037CE-0x00398B`.
- Base absoluta usada por el 68000: operando en `0x003664`.
- Cinco cadenas pequeñas del sistema permanecen en `0x000481-0x0004E9` porque las usa el arranque por separado.

Los bloques de ceros encontrados dentro del primer MiB no se consideran huecos libres. Muchos separan recursos comprimidos o son espacio de trabajo reservado por sus tablas; ocuparlos sin reconstruir cada archivo podría romper gráficos, música o circuitos.

## Zona ampliada segura

Cuando una traducción supera su hueco original, la herramienta amplía la ROM de 1 a 2 MiB y reserva:

- `0x100000-0x107FFF`: banco de textos recolocado, máximo 32768 bytes.
- `0x108000-0x1FFFFF`: libre para futuras ampliaciones del proyecto.

El importador reconstruye el banco, actualiza las 213 referencias, cambia la base del código 68000, ajusta el final de ROM del encabezado a `0x1FFFFF` y recalcula el checksum. Los desplazamientos siguen siendo palabras de 16 bits; por eso el banco se limita a menos de 32768 bytes.

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
