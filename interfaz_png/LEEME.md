# Interfaz, HUD y logo Virgin

Esta carpeta reúne los gráficos pequeños que faltaban tras el barrido final.

- `virgin/virgin_logo.png`: logotipo completo de Virgin Interactive, montado desde los recursos 186, 187 y 188.
- `menus`: fondos de preparar carrera, tienda, contraseña, cuatro participantes y resultados. Comparten el banco gráfico 3; las caras, coches y otros elementos móviles se superponen como sprites y ya están extraídos en sus carpetas correspondientes.
- `hud`: fuentes, números, indicadores, puntos de color y flechas empleados durante la carrera. Cada hoja conserva el orden nativo de sus tiles.
- `referencias`: capturas de BizHawk para entender dónde se usa cada pieza. No se reinsertan.

Los PNG editables conservan índices y paletas. No cambies sus dimensiones ni reorganices colores. Para generar una ROM aparte:

```powershell
python tools/export_interface.py --import-dir interfaz_png --output-rom roms_editadas/RockAndCasta-interfaz.md
```

La herramienta recalcula el checksum, mantiene el tamaño de 1 MiB y nunca sobrescribe la ROM original.
