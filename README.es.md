# atende-fisioterapia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Fisioterapia](guia/assets/banner.jpg)](https://inematds.github.io/atende-fisioterapia/guia/)

## 📖 Guía de uso

Landing y guía paso a paso (PT/EN/ES): **https://inematds.github.io/atende-fisioterapia/guia/** · [English](https://inematds.github.io/atende-fisioterapia/guia/en/) · [Español](https://inematds.github.io/atende-fisioterapia/guia/es/)

Atención al paciente de **una clínica de fisioterapia**, en Python 3 solo con la biblioteca estándar y SQLite: agenda de evaluación y sesiones, confirmación automática, lista de espera, **plan de tratamiento** (sesiones previstas × realizadas, alerta de abandono y de reevaluación), **ejercicios domiciliarios prescritos** con una biblioteca de 12 ejercicios animados (SVG; MP4 mediante HyperFrames para WhatsApp), recordatorio diario opt-in, registro de **adherencia y dolor** con alerta clínica, FAQ, cola humana, emergencia (192), campañas con la restricción del COFFITO y LGPD para datos de salud, registros, gestión de agenda, copia de seguridad, WhatsApp mediante la Evolution API, equipo por Telegram, exportación al Panel de Recuperación de Raio-X de Margem y entrega en Docker para VPS.

El contrato completo está en `docs/ESPECIFICACAO.md`. El chat del paciente está en `/`, la página del equipo en `/equipe` y cada ejercicio en `/exercicios/<id>`. El bot nunca da orientación clínica: explica solo lo que el fisioterapeuta prescribió y pasa el resto al equipo.

Proyecto hermano (molde): [`atende-clinica`](../atende-clinica). Diferencias resumidas al inicio de la especificación.

## Estructura

```
docs/ESPECIFICACAO.md      contrato congelado (secciones 0–25)
docs/DECISOES-ABERTAS.md   propuestas por defecto + preguntas que solo el dueño responde
docs/MAPA-RAIO-X.md        fuga del Raio-X → pieza del sistema
tests/                     98 pruebas de caja negra (pytest) + fixtures/clinica.json
exemplos/clinica.json      clínica de ejemplo (token TROQUE-ESTE-TOKEN; 12 ejercicios)
longrun/2026-10-05-fisio-v1/   goal, loop.env, prompts, congelar.sh, verificar-limites.sh, verificar-independente.py
FALHAS.md                  una línea por falla (fecha, qué se rompió, corrección mínima, prompt|infra)
```

**Estado (19/10/2026): sistema implementado, versión 0.7.0.** `python3 -m pytest -q tests/` → **98 passed**; `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK** en la entrega; verificación independiente → **INDEPENDENTE OK** (render MP4 mediante HyperFrames omitido). La implementación (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) fue producida por la ejecución larga descrita en "Cómo se construyó".

## Cómo ejecutarlo en tu entorno

**Requisitos previos:** Python 3.10+ (la aplicación solo usa la biblioteca estándar) y `pytest` para las pruebas; `git`; Docker para el despliegue en la VPS; opcionalmente Node ≥ 22, FFmpeg y Chromium para los videos MP4.

1. **Comprobar:** `python3 -m pytest -q tests/` → **98 passed**.
2. **Ejecutar en local:** `./atende serve --porta 8080 --dados ./dados` (detalles en "Ejecutar localmente"). Abre `/`, `/equipe` y `/exercicios/ponte` en el navegador.
3. **Personalizar:** ajusta `dados/clinica.json` (horarios, profesionales, servicios, FAQ, ejercicios) y cambia el token. Las 21 decisiones de comportamiento están en `docs/DECISOES-ABERTAS.md` (aceptadas como propuestas por defecto).
4. **Despliegue:** sigue "Despliegue en la VPS" más abajo, con tus credenciales de Evolution/WhatsApp y de Telegram.
5. **Videos MP4 de los ejercicios** (opcional, paso humano aún no ejecutado; requiere red, Node ≥ 22, FFmpeg y Chromium): `python3 tools/render-exercicios` genera `web/exercicios/<id>.mp4` (4 s, 720×720, sin audio) a partir de cada SVG — ver la sección 25 de la spec. Los MP4 no entran en Git; en la VPS, ejecuta el comando una vez o copia los archivos a la carpeta de `EXERCICIOS_MP4_DIR`. Sin MP4, los SVG animados siguen funcionando en la web.
6. **Revisión clínica:** los 12 ejercicios del ejemplo (pasos, errores comunes, cuidados, contraindicaciones, "detente si") y la lista de palabras de alerta de la spec (§6, regla 2) son un punto de partida — un fisioterapeuta los revisa antes de usarlos con pacientes reales.

## Cómo se construyó (método)

El sistema se hizo mediante ejecución larga, y el método sigue en el repositorio para quien quiera rehacerlo o adaptarlo:

1. **Decisiones respondidas** en `docs/DECISOES-ABERTAS.md` ("ok en todo"). Para cambiar algo marcado ⚠, ajusta `docs/ESPECIFICACAO.md` y `tests/` y comprueba `python3 -m pytest -q --collect-only | tail -1`.
2. **Contrato congelado:** `bash longrun/2026-10-05-fisio-v1/congelar.sh` grabó `hash-congelado.txt` con el hash de `tests/`, `pytest.ini`, de la spec y de los verificadores (`381b6510e90832d5`).
3. **Ejecución:** loop headless `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — lee `loop.env` (Codex `gpt-6-astra` mediante la suscripción, 20 ciclos × 30 min, 8 G, estancamiento 3, `CODEX_ARGS` con `network_access=true` porque las pruebas levantan un servidor en 127.0.0.1); cerró en 7 ciclos. Alternativas: `/goal` en Claude Code (`longrun/2026-10-05-fisio-v1/prompt-goal-claude.md`) o en el Codex TUI (`codex -c sandbox_workspace_write.network_access=true` y `prompt-goal-codex.md`).
4. **Controles y seguimiento:** `verificar-limites.sh` comprobaba el hash, el conteo de pruebas y el alcance de archivos (compara con el commit congelado, por lo que los cambios posteriores de documentación, como la guía, aparecen como fuera de alcance — es lo esperado). Seguimiento: `longrun/2026-10-05-fisio-v1/loop.log`, `state.md`, `progress.md`, `failures.md` y los commits de checkpoint (`git log --oneline`).
5. **Verificación independiente (nivel 4):** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. Levanta una clínica nunca vista, busca valores del fixture en el código, abre 3 SVG en un Chromium para probar que se mueven (y comprueba que los 12 tienen animaciones propias), renderiza un MP4 mediante HyperFrames y hace `docker build` + healthcheck. Sin Chromium/Playwright o sin HyperFrames, los pasos salen como `PULADO` (nunca como OK); en esta ronda el render MP4 salió `PULADO` (HyperFrames no instalado). El Chromium de snap sirve (los cuadros se graban dentro del repo, porque snap no ve `/tmp`). Validación del plan antes de la ejecución: `docs/VALIDACAO.md`.

Toda falla real va a `FALHAS.md` (una línea: fecha, qué se rompió, corrección mínima, prompt|infra).

## Despliegue en la VPS

Los comandos de esta sección son pasos del operador en la VPS.

1. Copia `.env.exemplo` a `.env` y mantén ese archivo privado (`chmod 600 .env`). Crea `dados/` y `backups/`; copia `exemplos/clinica.json` a `dados/clinica.json`, ajusta la clínica y cambia el token antes de iniciar. El compose persiste la base de datos y la configuración en `./dados`.
2. Rellena solo las integraciones que desees habilitar. Evolution usa `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` y `WEBHOOK_SEGREDO`. Telegram usa `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` y `TELEGRAM_SEGREDO`. Sin configuración, la salida es simulada. No uses `ATENDE_AGORA` en producción.
3. Ejecuta `docker compose up -d --build`. Comprueba `docker compose ps` y `docker compose logs atende`. El HEALTHCHECK consulta `/api/saude` con Python. La publicación queda solo en `127.0.0.1:8080`; el proceso dentro del contenedor acepta conexiones de la red del contenedor.
4. Configura tu proxy inverso (Nginx o Caddy) para reenviar el dominio al puerto local 8080, preservando ruta, cuerpo y headers, con certificado HTTPS. Define `PUBLIC_URL` como el origen público HTTPS, sin barra final. Accede a `/api/saude`, `/`, `/equipe` y `/exercicios/ponte`. Recrea el servicio tras cambios de entorno: `docker compose up -d --force-recreate`.
5. En la configuración de la instancia Evolution, registra el destino formado por `PUBLIC_URL` + `/webhook/evolution/<segredo>` (sustituye `<segredo>` por el `WEBHOOK_SEGREDO`) y selecciona el evento `MESSAGES_UPSERT`. La instancia debe ser la misma de `EVOLUTION_INSTANCIA`. No expongas la clave en el navegador.
6. Para Telegram, el operador registra el webhook usando el método `setWebhook` en la base `TELEGRAM_API_URL`, en la ruta `/bot<TELEGRAM_TOKEN>/setWebhook`, con los campos `url` (formado por `PUBLIC_URL` + `/webhook/telegram`) y `secret_token` igual a `TELEGRAM_SEGREDO`. El proxy debe preservar `X-Telegram-Bot-Api-Secret-Token`. Usa el grupo configurado en `TELEGRAM_CHAT_ID`; comandos disponibles: `/fila`, `/agenda`, `/alertas`, `/responder` y `/encerrar`.

Para los videos, el operador puede ejecutar `python3 tools/render-exercicios` fuera del contenedor (Node ≥ 22, FFmpeg, Chromium y red) o copiar MP4 ya renderizados a `web/exercicios/`. El compose monta esa carpeta en `/app/web/exercicios`, solo lectura. Define `EXERCICIOS_MP4_DIR=/app/web/exercicios` en el `.env`; si usas otra carpeta, ajusta también el volumen. Los MP4 quedan fuera de Git. Sin MP4 o sin `PUBLIC_URL`, la explicación sigue como texto con enlace.

Copia de seguridad diaria: crea `backups/`, restringe su acceso y añade al crontab del operador (cambia `/caminho/atende-fisioterapia` por el directorio instalado):

```cron
0 2 * * * cd /caminho/atende-fisioterapia && docker compose exec -T atende ./atende backup --dados /dados --saida /backups/clinica-$(date +\%F).zip >> backups/cron.log 2>&1
```

La copia incluye la configuración y un snapshot consistente del SQLite, incluso con el servidor encendido. Copia los archivos a un almacenamiento protegido fuera de la VPS y define la retención según la política de la clínica. Para restaurar, detén el servicio, restaura y reinicia:

```sh
docker compose stop atende
docker compose run --rm --no-deps atende ./atende restaurar --dados /dados --entrada /backups/clinica-AAAA-MM-DD.zip
docker compose up -d atende
```

Las confirmaciones, recordatorios, alertas y reenvíos dependen de llamadas periódicas a `POST /api/tarefas/rodar` con `X-Token`; no existe un planificador automático en el servidor. Configura un planificador interno autenticado para esa ruta. El token del equipo está en `dados/clinica.json`.

## Ejecutar localmente

```sh
./atende serve --porta 8080 --dados ./dados
```

El servidor imprime `PORTA=8080` y escucha solo en `127.0.0.1` por defecto; `--porta 0` elige un puerto libre. Python 3 y la biblioteca estándar son suficientes. Sin configuración previa, `exemplos/clinica.json` se copia a la carpeta de datos; personalízalo y cambia el token antes del uso real. Las integraciones son opcionales y se leen del entorno del proceso; `.env` lo carga el compose, no automáticamente la CLI.

Versión 0.7.0: página `/equipe` con agenda, registros, planes, prescripción, adherencia/dolor, biblioteca y alertas. El token queda solo en memoria en esta pestaña. `tools/render-exercicios` se escribió conforme a la sección 25; su ejecución y la revisión visual/clínica son pasos humanos. Usa `--so ponte` para un ejercicio o `--saida DIR` para elegir la carpeta de los MP4.
