---
name: creador-skills-trading
description: "Crea nuevas skills de trading a pedido o cuando un tema crece (estrategia propia, indicador, mercado nuevo, rutina, bot). Usar cuando el usuario diga 'crea una skill de...', 'guarda esta estrategia como skill', 'quiero una skill para...', o cuando en una sesión de trading surja conocimiento durable que merezca su propia skill."
---

# Creador de skills de trading

Meta-skill: fabrica otras skills de trading coherentes con el ecosistema del usuario. Responder en español, corto y directo.

## Ecosistema actual (no duplicar)
| Skill | Cubre |
|---|---|
| trading-completo | Análisis, MT5 vía Axi, reglas de riesgo base, bitácora, lecciones |
| catalogo-estrategias-trading | Catálogo de estrategias con reglas base |
| investigacion-estrategias-trading | Investigar y documentar estrategias |
| gestion-riesgo-avanzada | Lotes, drawdown, recuperación, proyecciones realistas |
| backtesting-estrategias | Backtests en Python con velas de MT5, métricas, walk-forward |
| bot-mt5-python | Bots con la librería MetaTrader5 (Windows), modo demo |
| checklist-entrada | Checklist con puntuación antes de cada operación |
| calendario-macro-noticias | Eventos macro, cómo operar alrededor de noticias |
| psicologia-disciplina | Tilt, rutinas, reglas de parada |
| revision-semanal-trading | Revisión semanal con estadísticas |
| cuentas-fondeo-prop | Retos de fondeo (prop firms) |
| estrategia-ruptura-asiatica-oro | Ruptura del rango asiático en oro H1 (estado: backtest) |
| scalping-micro-oro | Scalping M1 / muchas operaciones pequeñas (estado: DESCARTADA por spread) |

Antes de crear, revisar `ls ~/.claude/skills ~/.claude/skills/synced/*/` por si ya existe algo parecido. Si existe, **proponer editar esa** en lugar de crear otra.

## Flujo
1. **Entender** (máx. 3 preguntas si falta info): ¿qué debe hacer?, ¿cuándo debe activarse?, ¿qué mercado/temporalidad?, ¿usa herramientas (Axi MT5, web, Python)?
2. **Nombrar**: kebab-case en español, 2-4 palabras (`estrategia-ruptura-londres`, `indicador-vwap`).
3. **Redactar** con la plantilla `templates/SKILL_TEMPLATE.md`. Reglas:
   - `description` es lo que hace que la skill se active: decir QUÉ hace y CUÁNDO usarla, con frases que el usuario diría.
   - Cuerpo < 300 líneas; detalles largos van en `references/*.md`; cálculos repetibles en `scripts/*.py`.
   - Instrucciones accionables (pasos, reglas medibles), no ensayos.
   - Si es una estrategia: entrada, SL, TP, filtros, sesión, invalidación, y estado de validación (`sin probar` / `backtest` / `demo` / `validada`).
4. **Incluir siempre el bloque de seguridad** (copiar tal cual):
   ```
   ## Reglas de seguridad (heredadas)
   - Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
   - Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
   - Nunca inventar precios: consultarlos en vivo. Sin garantías; Claude no es asesor financiero.
   - Una estrategia sin backtest + demo no se usa en real.
   ```
5. **Crear** en `~/.claude/skills/<nombre>/SKILL.md` (+ references/scripts si aplica). Probar cualquier script con datos de ejemplo antes de entregar.
6. **Empaquetar** para que no se pierda (el contenedor de la nube es temporal):
   ```bash
   cd ~/.claude/skills && zip -r /home/user/skills-trading/<nombre>.zip <nombre>
   ```
   Decir al usuario que la suba en claude.ai → Configuración → Capacidades/Skills → subir skill.
   **Si existe el repo del plugin** (`trading-skills-plugin`): copiar la carpeta a `plugins/trading-pro/skills/`, subir la versión (+0.1.0) en `plugin.json` y `marketplace.json`, commit y push. El usuario actualiza con `/plugin marketplace update trading-skills`.
7. **Actualizar** la tabla "Ecosistema actual" de esta skill con la nueva fila.

## Cuándo proponer una skill nueva sin que la pidan
- El usuario repite la misma explicación/estrategia en 2+ sesiones.
- Una sección de `trading-completo` supera ~40 líneas.
- Se valida una estrategia en backtest/demo → guardarla como skill propia con sus métricas.
Proponer en una línea; crear solo si acepta.

## Ideas de skills futuras
estrategia-propia-<nombre>, indicador-<nombre>, sesion-asiatica-oro, correlaciones-intermercado, opciones-basico, cripto-basico, alertas-precio, plan-de-trading-personal.
