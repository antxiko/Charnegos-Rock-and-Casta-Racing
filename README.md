# CHARNEGO'S ROCK & CASTA RACING

> **Arranca el cacharro, sube el metal y aparta, que vamos sin frenos.**

Aquí hemos abierto en canal el **Rock 'n' Roll Racing europeo de Mega Drive** para sacar todo lo que lleva debajo del capó. Coches, caretos, circuitos, voces, música y textos: todo fuera, todo editable y todo listo para volver a meterlo en una ROM nueva.

Esto no es un emulador ni una ROM pirata metida debajo de la gabardina. Es una caja de herramientas para que cada cual destripe su propia copia, la tunee a su gusto y se monte el campeonato más macarra de la galaxia.

## ¿Qué se puede mangonear?

- **Los bólidos:** 225 vistas de coches con sus paletas, preparadas para meter la furgoneta del Equipo A, el Coche Fantástico o el trasto que te salga del tubo de escape.
- **Los caretos:** 15 retratos de pilotos y rivales en PNG editable.
- **Las voces del notas:** 42 samples PCM de 8 bits a 7778 Hz, incluidos los gritos de quién va primero y quién está a punto de reventar.
- **Los circuitos:** los 72 mapas, sus tiles, decorados, capas y un editor visual para no acabar montando la pista como un puesto del mercadillo.
- **La chicharra:** las seis músicas del driver Sound Images v1.20, extraídas como secuencia nativa, MIDI, VGM y proyectos de Furnace Tracker.
- **La parrafada:** 214 textos de menús, pilotos, planetas, tienda, finales y créditos en un único fichero editable.
- **La entrada triunfal:** logos de Interplay y Blizzard, fondo del título y letras saltarinas, cada cosa en su PNG indexado y con su paleta.
- **El final del campeonato:** hangar, planetas, ciudad, ceremonia, vehículos y efectos separados por capas, con las fases reales de sus paletas animadas.

## Antes de darle al botón gordo

Necesitas:

- Python 3.10 o posterior;
- una copia europea y legal de la ROM llamada `Rock 'n' Roll Racing (Europe).md`;
- las dependencias de `requirements.txt`;
- BizHawk si quieres comprobar el invento dentro del juego;
- Furnace Tracker si vas a meter mano a los módulos `.fur`.

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Y ahora sí, abre el taller:

```powershell
python tools/export_cars.py
python tools/export_faces.py
python tools/export_samples.py
python tools/export_all_tracks.py
python tools/export_music.py --export
python tools/export_texts.py
python tools/export_intro.py
python tools/export_ending.py
```

Cada herramienta deja sus resultados en una carpeta separada. La ROM original se mira, pero no se soba: cualquier reinserción genera otra ROM y recalcula su checksum.

## Música para atronar el barrio

Para fabricar los VGM y los proyectos de Furnace hace falta [vgm2fur](https://github.com/std282/vgm2fur):

```powershell
python -m pip install "git+https://github.com/std282/vgm2fur.git"
python tools/export_music_vgm.py
python tools/convert_vgm_to_furnace.py
```

Los `.fur` sirven para abrir las canciones en Furnace, ver los canales del YM2612 y meterles mano. Para devolver música a la ROM se utiliza el importador MIDI o el editor nativo generado por `export_music.py`. La conversión directa de cualquier `.fur` de vuelta al driver todavía no está hecha; tampoco vamos a vender humo como el cuñado del taller.

## Traducir la chapa del juego

```powershell
python tools/export_texts.py
```

Eso saca 214 cadenas en `textos/textos.json`. Abre `textos/EDITOR.html`, carga el JSON y cambia lo que quieras. Después arrastra el fichero descargado sobre `textos/APLICAR_TEXTOS.cmd`.

Hay que respetar el ancho de cada línea porque esto es una Mega Drive, no una marquesina del Carrefour. La fuente original tampoco tiene `Ñ` ni vocales con tilde: toca escribir `N` y tirar sin acentos hasta que ampliemos el juego de caracteres.

## Aquí no se reparte género robado

El repositorio contiene **código y documentación propia**. No incluye:

- ROMs;
- savestates;
- gráficos extraídos;
- WAV, VGM, MIDI ni módulos Furnace generados;
- ningún otro recurso original del juego.

Cada colega debe poner su propia ROM y generar el material en su máquina. Los scripts comprueban el SHA-256 de la versión europea conocida antes de tocar un solo byte. Si les das otra cosa, se plantan y te mandan a paseo antes de liarla parda.

## ¿Esto está probado o va con bridas?

Las extracciones principales tienen ida y vuelta binaria comprobada. Los coches se han contrastado con VRAM, CRAM y la tabla de sprites de BizHawk. Los textos vuelven a la ROM sin alterar nada cuando no se editan. Las canciones se han cargado desde la RAM Z80 y las ROM modificadas actualizan el checksum.

Eso no convierte cada prueba técnica en una partida completa. Cuando una comprobación es de bytes, es de bytes; cuando es de BizHawk, es de BizHawk. Aquí cada tornillo lleva su etiqueta y nadie dice «en hardware va fino» hasta enchufarlo de verdad.

## Los papeles del coche

Código publicado con licencia MIT. **Rock 'n' Roll Racing**, sus gráficos, músicas, voces y demás recursos pertenecen a sus respectivos propietarios.

Proyecto comunitario de **Charnego Translations**, sin relación con Blizzard Entertainment, Interplay ni Electronic Arts.

Ahora ponte los guantes, abre el capó y no rayes la pintura, figura.
