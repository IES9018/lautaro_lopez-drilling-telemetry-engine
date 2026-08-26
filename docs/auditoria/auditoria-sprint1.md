# Auditoría crítica de código asistido por IA — Sprint 1

**Proyecto:** `lautaro_lopez-drilling-telemetry-engine`  
**Institución:** IES 9-018 · PP3 · Ciclo 2026  
**Profesor:** Paulo Alvarez  
**Sprint:** 1 (24 ago – 18 sep 2026)  
**Responsable del informe:** lautaro_lopez  
**SSOT de contraste:** [`SPEC.md`](../../SPEC.md)  
**Gobernanza:** [`.cursor/rules/`](../../.cursor/rules/)

---

## 1. Objetivo

Documentar de forma auditable:

- Alucinaciones o errores conceptuales introducidos por agentes de IA.
- Errores de **convergencia / estabilidad numérica** (RK4, UKF, SSI).
- Malas prácticas (tipado, secretos, cajas negras, acoplamiento entre dominios).
- La **corrección manual** aplicada y quién la validó.

Este informe aporta a la rúbrica de evaluación (**10% Documentación / Auditoría crítica de IA**).

---

## 2. Metodología de revisión crítica

1. Identificar el fragmento generado o asistido por IA (PR, archivo, función).
2. Contrastar ecuaciones, unidades y constantes contra `SPEC.md` (secciones 2.x).
3. Ejecutar tests unitarios, property (Hypothesis) y de estabilidad numérica cuando aplique.
4. Clasificar el hallazgo:
   - **alucinación** — afirmación o fórmula incorrecta inventada por el modelo
   - **convergencia numérica** — inestabilidad, orden incorrecto, covarianza no PSD, NaN/Inf
   - **mala práctica** — tipado laxo, acoplamiento de dominios, caja negra, secretos, etc.
5. Registrar corrección manual y evidencia (test, commit, revisión).
6. Cerrar el hallazgo solo cuando haya verificación humana explícita.

---

## 3. Registro de hallazgos

| ID | Fecha | Componente / ruta | Tipo | Descripción | Corrección manual aplicada | Evidencia (test/PR) | Responsable | Estado |
|----|-------|-------------------|------|-------------|----------------------------|---------------------|-------------|--------|
| A-001 | YYYY-MM-DD | `src/engine/...` | alucinación \| convergencia numérica \| mala práctica | … | … | … | lautaro_lopez | abierto \| cerrado |
| A-002 |  |  |  |  |  |  |  |  |

> Agregar una fila por hallazgo. No borrar filas históricas: marcar estado `cerrado`.

### Plantilla de detalle (copiar por hallazgo relevante)

#### Hallazgo A-00X

- **Tipo:**
- **Agente / herramienta:**
- **Qué generó la IA (resumen):**
- **Por qué es incorrecto (contraste con SPEC):**
- **Impacto potencial:** (seguridad / NPT diagnóstico / crash numérico / deuda técnica)
- **Corrección aplicada:**
- **Verificación:** (comandos, tests, revisión de ecuaciones)
- **Lección aprendida:**

---

## 4. Resumen cuantitativo del Sprint 1

| Métrica | Valor |
|---------|-------|
| Total de hallazgos registrados | 0 |
| Alucinaciones | 0 |
| Convergencia numérica | 0 |
| Malas prácticas | 0 |
| Hallazgos cerrados | 0 |
| Hallazgos abiertos | 0 |
| PRs con código IA auditado | 0 |

---

## 5. Lecciones aprendidas

<!-- Completar al cierre del sprint. Ejemplos de temas: unidades, signos en Stribeck, retardo MWD, PSD de P, isolation de dominios. -->

1. …
2. …

---

## 6. Declaración de cierre (al finalizar el Sprint 1)

- [ ] Todos los hallazgos críticos de física/UKF están cerrados o tienen mitigación documentada.
- [ ] No quedan fórmulas en `develop` sin contraste contra `SPEC.md`.
- [ ] La cobertura y SAST del sprint cumplen los umbrales acordados (ver `INSTRUCTIONS.md` / rúbrica).

**Firma / fecha de cierre:** __________________
