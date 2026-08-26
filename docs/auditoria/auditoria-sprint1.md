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
| A-001 | 2026-08-25 | `src/engine/physics/friction_models.py` | convergencia numérica | SPEC §2.3 usa \(T_c+(T_s-T_c)e^{-(\|\omega\|/\omega_s)^\delta}+b\omega\) sin regularización en ω=0 (discontinua / no diferenciable en el signo). La implementación Sprint 1 usa forma regularizada con `tanh(ω/ω_ε)` y decaimiento `exp(-γ\|ω\|)` para estabilidad numérica del lazo RK4. | Documentar como variante explícita; tests de imparidad, reposo T(0)=0 y régimen asintótico. No es alucinación: es decisión de regularización. | `tests/unit/test_friction_models.py` | lautaro_lopez | cerrado |
| A-002 | 2026-08-25 | `src/engine/physics/drillstring_fem.py` | convergencia numérica | SPEC §2.2 indica “velocidad o torque prescrito” en superficie sin fijar la ley de accionamiento. Se modela top-drive como \(T_{drive}=c_{drive}(u_{top}-\omega_0)\) (amortiguamiento proporcional al error de velocidad). | Documentar en `MODELO_MATEMATICO.md`; validar con equilibrio rígido (`test_steady_state_torque_balance`). Decisión de modelado explícita, no alucinación. | `tests/unit/test_drillstring_fem.py` · docs/arquitectura/MODELO_MATEMATICO.md | lautaro_lopez | cerrado |
| A-003 | 2026-08-25 | `src/engine/kalman/ukf_estimator.py`, `sigma_points.py` | convergencia numérica | SPEC §2.5.3 no fija si `update` regenera sigma points desde \((x^-,P^-)\) o reutiliza los propagados por `predict`. Se adopta reuso de sigma points propagados (Van der Merwe), Cholesky+jitter con backoff, re-simetrización de \(P\), y `np.linalg.solve` en vez de inversa explícita para \(K\). | Documentar en `MODELO_MATEMATICO.md` §8; tests de simetría/PSD y consistencia 3σ. | `tests/unit/test_ukf_estimator.py` · `tests/unit/test_sigma_points.py` | lautaro_lopez | cerrado |
| A-004 | 2026-08-25 | `src/engine/simulator/well_generator.py` | convergencia numérica | Integración a ~1000 Hz (`dt_internal=1e-3`) vs muestreo de telemetría 100 Hz (`dt=0.01`). Si `dt` no es múltiplo exacto de `dt_internal`, se usa `n_sub=round(dt/dt_internal)` y `sub_dt=dt/n_sub` para conservar el horizonte `dt` a costa de un paso RK4 ligeramente distinto del nominal. | Documentar trade-off; preferir `dt` múltiplo de `dt_internal` en escenarios de producción. | `tests/integration/test_well_generator.py` | lautaro_lopez | cerrado |
| A-008 | 2026-08-26 | `tests/property/_torsional_energy.py` | convergencia numérica | Helper QA de energía torsional \(E=\tfrac12\sum I_i\omega_i^2+\tfrac12\theta^\mathsf{T}K\theta\) + aserción \(dE/dt\le\varepsilon\) con \(u_{top}=wob=0\). La tolerancia \(\varepsilon=10^{-4}\) J/s absorbe error local RK4; no es conservación exacta sin disipación. | Documentar fórmula vs SPEC §5.3; property test Hypothesis derandomizado. | `tests/property/test_physics_invariants.py` | lautaro_lopez | cerrado |

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
| Total de hallazgos registrados | 5 |
| Alucinaciones | 0 |
| Convergencia numérica | 5 |
| Malas prácticas | 0 |
| Hallazgos cerrados | 5 |
| Hallazgos abiertos | 0 |
| PRs con código IA auditado | 5 |

---

### Detalle A-001

- **Tipo:** convergencia numérica (regularización intencional)
- **Agente / herramienta:** Physics Engine Agent (Cursor)
- **Qué generó la IA (resumen):** `stribeck_friction_torque` con `tanh` y `gamma`
- **Por qué difiere del SPEC:** SPEC §2.3 no incluye `ω_ε`; la forma clásica con signo(ω) es discontinua en 0
- **Impacto potencial:** sin regularización, RK4 cerca de stick puede oscilar / no derivar bien
- **Corrección aplicada:** aceptar variante regularizada documentada; tests de imparidad y T(0)=0
- **Verificación:** pytest unitario de fricción + contraste manual de fórmula
- **Lección aprendida:** toda desviación de SPEC §2 debe registrarse aquí aunque sea físicamente motivada

### Detalle A-002

- **Tipo:** convergencia numérica (decisión de modelado)
- **Agente / herramienta:** Physics Engine Agent (Cursor)
- **Qué generó la IA (resumen):** \(T_{drive}=c_{drive}(u_{top}-\omega_0)\) en `build_state_derivative`
- **Por qué difiere del SPEC:** SPEC §2.2 no fija la ley de accionamiento del top-drive
- **Impacto potencial:** dinámica de superficie distinta a un torque prescrito puro
- **Corrección aplicada:** documentar en `MODELO_MATEMATICO.md`; test de equilibrio rígido
- **Verificación:** `test_steady_state_torque_balance`
- **Lección aprendida:** toda BC no literal del SPEC requiere ADR/auditoría + test de invariante

### Detalle A-003

- **Tipo:** convergencia numérica (estabilidad numérica del UKF)
- **Agente / herramienta:** Physics & State Estimation Agent (Cursor)
- **Qué generó la IA (resumen):** reuso de sigma points propagados; Cholesky+jitter; `solve` para \(K\)
- **Por qué difiere del SPEC:** SPEC §2.5.3 no especifica regeneración vs reuso ni jitter
- **Impacto potencial:** drift de \(P\) no-PSD / inversión inestable de \(P_{zz}\)
- **Corrección aplicada:** documentar en `MODELO_MATEMATICO.md` §8; tests PSD/simetría/3σ
- **Verificación:** `test_predict_preserves_symmetry_and_psd`, `test_consistency_error_within_three_sigma`
- **Lección aprendida:** toda decisión de estabilización del filtro debe registrarse y cubrirse con test

### Detalle A-004

- **Tipo:** convergencia numérica (trade-off simulación)
- **Agente / herramienta:** Physics & Simulation Engine (Cursor)
- **Qué generó la IA (resumen):** `n_sub=round(dt/dt_internal)`, `sub_dt=dt/n_sub` en `WellSimulator.step`
- **Por qué es un trade-off:** 1000 Hz interno vs 100 Hz de telemetría; `dt` no siempre múltiplo exacto
- **Impacto potencial:** error local de paso RK4 vs horizonte de tiempo exacto
- **Corrección aplicada:** conservar horizonte `dt`; preferir múltiplos exactos en configs
- **Verificación:** `tests/integration/test_well_generator.py`
- **Lección aprendida:** documentar política de submuestreo cuando haya dos tasas (física vs telemetría)

### Detalle A-008

- **Tipo:** convergencia numérica (invariante de energía en property test)
- **Agente / herramienta:** DevOps/QA Agent (Cursor)
- **Qué generó la IA (resumen):** helper \(E=\tfrac12\sum I_i\omega_i^2+\tfrac12\theta^\mathsf{T}K\theta\) y aserción \(dE/dt\le 10^{-4}\) con \(u_{top}=wob=0\)
- **Contraste SPEC:** §5.3 pide que la energía no crezca artificialmente sin potencia externa; la tolerancia absorbe error local RK4 y la disipación física (damping / top-drive a \(u_{top}=0\)) es esperada
- **Impacto potencial:** falso negativo flaky si \(\varepsilon\) es demasiado estricto
- **Corrección aplicada:** \(\varepsilon\) documentado; Hypothesis `derandomize=True`; helper solo en `tests/property/`
- **Verificación:** `tests/property/test_physics_invariants.py`
- **Lección aprendida:** invariantes de energía van en tests QA, no en producción, hasta que el dominio physics exportue un helper oficial


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
