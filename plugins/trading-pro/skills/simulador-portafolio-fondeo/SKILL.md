---
name: simulador-portafolio-fondeo
description: "Simula todas las estrategias validadas operando juntas (portafolio) y estima rendimiento anual, caída máxima y probabilidad de aprobar o quemar un reto de cuenta de fondeo, según el riesgo por operación. Usar cuando el usuario pregunte '¿cuánto puedo ganar al año?', '¿paso un reto de fondeo?', '¿qué riesgo uso?', '¿cuánto tardo en llegar a X?', 'todas las estrategias juntas', o antes de comprar un reto."
---

# Simulador de portafolio y retos de fondeo

Español, corto. Combina las operaciones (en R) de las estrategias validadas y aplica un riesgo fijo por operación.

## Uso
`RIESGO=0.005 python3 -I scripts/portafolio.py config.json <carpeta_con_megalab.py>` — usa el mismo `config.json` del megalab (`laboratorio-estrategias`). Cambiar `RIESGO` (0.0025, 0.005, 0.01) para comparar. Para añadir o quitar estrategias, editar el diccionario `EST` del script.

## Resultado 2026-11-23 (RSI2 en 4 índices + Donchian oro/ETH/BTC + ruptura asiática oro)
| Riesgo | Anual compuesto | Caída máx. | Reto +10% / −10% | Reto +8% / −5% |
|---|---|---|---|---|
| 0.5% | +12.5% | 6.1% | aprueba 99.7% (~8.6 meses) | aprueba 94% |
| 1% | +25.8% | 11.9% | aprueba 94% (~4 meses) | **quema 23%** |
Años 2022-2025 con 0.5%: +2.2%, +6.0%, +7.3%, +6.2% (2026 +43.5% inflado: la ruptura asiática solo tiene datos de 2026).

## Cómo leerlo (honestidad obligatoria)
- **Es un techo optimista**: las estrategias se eligieron mirando estos datos (sesgo de selección) y el Monte Carlo supone operaciones independientes y sin el tope de 2% abierto. Esperar **~la mitad** en real (la literatura sobre IBS indica que en vivo rinde ~50-55% del backtest).
- No incluye swap ni deslizamiento en noticias.
- Conclusión práctica: **0.5% de riesgo es el punto dulce para un reto con pérdida máx. 5%**; 1% solo con pérdida máx. 10% y aceptando más riesgo de quemar.
- Antes de comprar un reto: 30-50 operaciones reales en la demo de $100k deben confirmar expectativa positiva (ver `plan-de-trading-personal`).

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación (0.5% en la demo de $100k), 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Sin garantías; resultados simulados no son resultados futuros. Claude no es asesor financiero.
