# Notas de producción — v001

## Estructura (160 compases a 156 BPM)

| Sección | Compases | Función |
|---|---:|---|
| intro | 1–16 | energía 0.20, roles: texture, harmony, latin_perc |
| groove | 17–32 | energía 0.45, roles: drums, latin_perc, bass, harmony |
| cumbia_tease | 33–48 | energía 0.56, roles: drums, latin_perc, bass, lead |
| build_1 | 49–64 | energía 0.70, roles: drums, latin_perc, bass, arp, lead |
| drop_1 | 65–96 | energía 0.91, roles: drums, latin_perc, bass, harmony, arp, lead |
| break | 97–112 | energía 0.36, roles: latin_perc, harmony, lead |
| build_2 | 113–128 | energía 0.80, roles: drums, latin_perc, bass, arp, lead |
| final_drop | 129–152 | energía 1.00, roles: drums, latin_perc, bass, harmony, arp, lead |
| outro | 153–160 | energía 0.44, roles: drums, latin_perc, bass |

## Orden recomendado en Waveform

1. Importar cada MIDI en una pista separada y fijar 156 BPM.
2. Drum rack GM: kick 36, clap 39, closed hat 42, open hat 46, crash 49.
3. Percusión GM: conga 62/63/64, cowbell 56 y güiro 73/74 (según mapeo del instrumento, verificar).
4. Asignar sonido mono a `bass.mid`; sidechain sutil del kick.
5. Asignar a `lead.mid` sonido sintético con identidad sonidera, sin replicar la melodía comercial.
6. Automatizar filtro de arp y ancho del pad en build y break.
7. Render preliminar solo después de comprobar que todas las pistas suenan; mantener margen en master.

## Qué NO está hecho

No hay audio renderizado, diseño sonoro real, automatizaciones insertadas en Waveform, clon de la grabación original ni integración DAW confirmada.
