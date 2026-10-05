# atende-fisioterapia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Fisioterapia](guia/assets/banner-es.jpg)](https://inematds.github.io/atende-fisioterapia/guia/es/)

## 📖 Guía de uso

Landing y guía paso a paso: **https://inematds.github.io/atende-fisioterapia/guia/es/** · [Português](https://inematds.github.io/atende-fisioterapia/guia/) · [English](https://inematds.github.io/atende-fisioterapia/guia/en/)

Atención al paciente de **una clínica de fisioterapia**, en Python 3 solo con la biblioteca estándar y SQLite: agenda de evaluación y sesiones, confirmación automática, lista de espera, **plan de tratamiento** (sesiones previstas × realizadas, alerta de abandono y de reevaluación), **ejercicios domiciliarios prescritos** con una biblioteca de 12 ejercicios animados (SVG; MP4 con HyperFrames para WhatsApp), recordatorio diario opt-in, registro de **adherencia y dolor** con alerta clínica, FAQ, cola humana, emergencia (192, el número de emergencias de Brasil), campañas con la salvaguarda del COFFITO (el consejo brasileño de fisioterapia) y LGPD (la ley brasileña de protección de datos) de datos de salud, registros, gestión de agenda, respaldo, WhatsApp por la Evolution API, equipo por Telegram, exportación al Panel de Recuperación de Raio-X de Margem y entrega en Docker para un VPS.

**Estado (05/10/2026): planificado, no implementado.** Lo que existe es el contrato, 98 pruebas de aceptación de caja negra, las decisiones con propuestas por defecto, el mapa de las fugas de Raio-X y la carpeta de ejecución larga, listos para que cualquiera ejecute la implementación en su propio entorno con un agente.

El contrato completo está en `docs/ESPECIFICACAO.md`. El chat del paciente queda en `/`, la página del equipo en `/equipe` y cada ejercicio en `/exercicios/<id>`. El bot nunca da orientación clínica: solo explica lo que el fisioterapeuta prescribió y pasa el resto al equipo.

Nota: los docs, las pruebas y los comandos del chat del bot están en portugués. LGPD, COFFITO y `192` son de Brasil; en otro país la clínica debe cambiarlos por la ley de privacidad, el consejo profesional y el número de emergencias locales.

Proyecto hermano (el molde): [`atende-clinica`](https://inematds.github.io/atende-clinica/guia/es/) (93/93 pruebas). Las diferencias están resumidas al inicio de la especificación. Las reglas de negocio vienen de [Raio-X de Margem](https://inematds.github.io/raio-x-margem/guia/es/).

## Estructura

```
docs/ESPECIFICACAO.md      contrato congelado (secciones 0–25)
docs/DECISOES-ABERTAS.md   propuestas por defecto + preguntas que solo el dueño responde
docs/MAPA-RAIO-X.md        fuga de Raio-X → pieza del sistema
docs/VALIDACAO.md          validación adversarial del plan (9 problemas, 3 bloqueaban)
tests/                     98 pruebas de caja negra (pytest) + fixtures/clinica.json
exemplos/clinica.json      clínica de ejemplo (token TROQUE-ESTE-TOKEN; 12 ejercicios)
longrun/2026-10-05-fisio-v1/   goal, loop.env, prompts, congelar.sh, verificar-limites.sh, verificar-independente.py
FALHAS.md                  una línea por falla (fecha, qué se rompió, corrección mínima, prompt|infra)
```

La implementación (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) la produce la ejecución larga descrita abajo.

## Cómo ejecutarlo en tu entorno

Esta sección es del dueño del proyecto; el implementador agrega las suyas (ejecución local, despliegue en el VPS) sin reescribirla.

**Requisitos:** Python 3.10+ y `pytest` (`python3 -m pytest --version`); `git`; para el loop headless, el Codex CLI con sesión iniciada por suscripción y `~/projetos/execucao-longa` (método, `tools/loop-longrun.sh`); para la verificación final, Docker y, opcionalmente, Chromium/Playwright y Node ≥ 22 + FFmpeg (HyperFrames).

1. **Responde las decisiones** en `docs/DECISOES-ABERTAS.md` ("ok em tudo", todo bien, vale). Si cambias algo marcado con ⚠, ajusta `docs/ESPECIFICACAO.md` y `tests/` antes del paso 2 y revisa `python3 -m pytest -q --collect-only | tail -1`.
2. **Congela el contrato:** `git status` limpio y luego `bash longrun/2026-10-05-fisio-v1/congelar.sh` (graba `hash-congelado.txt` con el hash de `tests/`, `pytest.ini`, la especificación y los verificadores, y hace el commit).
3. **Ejecuta** por uno de tres caminos:
   - **Loop headless (recomendado):** `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — lee `loop.env` (Codex `gpt-6-astra`, 20 ciclos × 30 min, 8 G, estancamiento 3, `CODEX_ARGS` con `network_access=true` porque las pruebas levantan un servidor en 127.0.0.1), revierte el ciclo que toque un archivo protegido y hace el commit de checkpoint.
   - **`/goal` en Claude Code:** sigue `longrun/2026-10-05-fisio-v1/prompt-goal-claude.md` (una sesión nueva abierta en esta carpeta).
   - **`/goal` en el Codex TUI:** `codex -c sandbox_workspace_write.network_access=true` en esta carpeta y pega `longrun/2026-10-05-fisio-v1/prompt-goal-codex.md`.
4. **Sigue el avance:** `tail -f longrun/2026-10-05-fisio-v1/loop.log` (headless) y los archivos `state.md`, `progress.md`, `failures.md`; `git log --oneline` muestra los checkpoints. Listo = `python3 -m pytest -q tests/` → **98 passed** y `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK**. El loop se detiene solo por estancamiento (3 ciclos sin avance) o por el tope.
5. **Verificación independiente (nivel 4), después del "concluido":** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. Levanta una clínica nunca vista, busca valores del fixture en el código, abre 3 SVG en un Chromium para probar que se mueven (y comprueba que los 12 tienen animaciones propias), renderiza un MP4 con HyperFrames y hace `docker build` + healthcheck. Sin Chromium/Playwright o sin HyperFrames, esas etapas salen como `PULADO` (omitido), nunca como OK; instálalos y ejecuta de nuevo si quieres la prueba completa. Docker es obligatorio. El Chromium de snap sirve (los cuadros se graban dentro del repo, porque el snap no ve `/tmp`). El resultado de la validación independiente del plan está en `docs/VALIDACAO.md`. Abre también `/`, `/equipe` y `/exercicios/ponte` en el navegador.
6. **Videos MP4 de los ejercicios** (paso humano; necesita red, Node ≥ 22, FFmpeg y Chromium): `python3 tools/render-exercicios` genera `web/exercicios/<id>.mp4` (4 s, 720×720, sin audio) a partir de cada SVG — ver la sección 25 de la especificación. Los MP4 no entran en Git; en el VPS, ejecuta el comando una vez o copia los archivos a la carpeta de `EXERCICIOS_MP4_DIR`.
7. **Revisión clínica:** los 12 ejercicios del ejemplo (pasos, errores comunes, cuidados, contraindicaciones, "detente si") y la lista de palabras de alerta de la especificación (§6, regla 2) son un punto de partida — un fisioterapeuta los revisa antes de usarlos con un paciente real.

Toda falla real va a `FALHAS.md` (una línea: fecha, qué se rompió, corrección mínima, prompt|infra).
