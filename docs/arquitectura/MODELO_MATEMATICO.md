# Modelo matemático — Sarta torsional (espacio de estados) y SSI

**Proyecto:** `lautaro_lopez-drilling-telemetry-engine`  
**SSOT:** [`SPEC.md`](../../SPEC.md) §2  
**Código:** [`drillstring_fem.py`](../../src/engine/physics/drillstring_fem.py), [`ssi_calculator.py`](../../src/engine/kalman/ssi_calculator.py), [`sigma_points.py`](../../src/engine/kalman/sigma_points.py), [`ukf_estimator.py`](../../src/engine/kalman/ukf_estimator.py)

---

## 1. Vector de estado interleaved

Para \(N\) nodos, el estado de dimensión \(2N\) es:

\[
\mathbf{x}
=
\begin{bmatrix}
\theta_0 & \omega_0 & \theta_1 & \omega_1 & \cdots & \theta_{N-1} & \omega_{N-1}
\end{bmatrix}^{\mathsf{T}}
\]

con \(\omega_i = \dot{\theta}_i\). Extracción por slicing: `theta = state[0::2]`, `omega = state[1::2]`.

Relación con SPEC §2.2: misma información que el apilado \([\boldsymbol{\theta};\boldsymbol{\omega}]\), en layout intercalado para locality en el lazo RK4.

---

## 2. Discretización lumped y matrices \(I\), \(C\), \(K\)

Partiendo de la PDE torsional (SPEC §2.1):

\[
\rho J\,\partial_{tt}\theta = GJ\,\partial_{xx}\theta - c\,\partial_t\theta
\]

cadena uniforme de longitud \(L\):

\[
dx = \frac{L}{N-1},
\quad
I_i = \rho J\, dx,
\quad
k_i = \frac{GJ}{dx}
\]

- \(\mathbf{I} = \mathrm{diag}(I_0,\ldots,I_{N-1})\) (en código: vector `inertia`).
- \(\mathbf{C} = \mathrm{diag}(c_0,\ldots,c_{N-1})\) — `build_damping_matrix`.
- \(\mathbf{K}\) tridiagonal simétrica — `build_stiffness_matrix`:

\[
K_{i,i} = k_{i-1}+k_i,\quad
K_{i,i+1}=K_{i+1,i}=-k_i
\]

(en bordes, un solo vecino).

Forma de segundo orden:

\[
\mathbf{I}\,\ddot{\boldsymbol{\theta}}
+
\mathbf{C}\,\dot{\boldsymbol{\theta}}
+
\mathbf{K}\,\boldsymbol{\theta}
=
\mathbf{T}_{\mathrm{ext}}(\boldsymbol{\omega}, u_{\mathrm{top}}, \mathrm{WOB})
\]

---

## 3. Condiciones de borde

### 3.1 Top drive (nodo 0) — control de velocidad

Simplificación de modelado (auditoría **A-002**):

\[
T_{\mathrm{drive}} = c_{\mathrm{drive}}\,(u_{\mathrm{top}} - \omega_0)
\]

donde \(u_{\mathrm{top}}\) es la velocidad angular de referencia [rad/s] y \(c_{\mathrm{drive}}>0\).

### 3.2 Broca / BHA (nodo \(N-1\)) — Stribeck vía WOB

\[
T_c = \mu_c \cdot (\mathrm{WOB}_{\mathrm{kN}}\cdot 1000)\cdot r_{\mathrm{bit}},
\quad
T_s = \mu_s \cdot (\mathrm{WOB}_{\mathrm{kN}}\cdot 1000)\cdot r_{\mathrm{bit}}
\]

Torque de fricción: `stribeck_friction_torque` (forma regularizada, A-001). En el balance nodal:

\[
T_{\mathrm{ext},N-1} = -T_{\mathrm{bit}}(\omega_{N-1})
\]

---

## 4. Derivada de estado \(f(t,\mathbf{x},u_{\mathrm{top}},\mathrm{wob})\)

\[
\begin{aligned}
\dot{\theta}_i &= \omega_i \\
I_i\,\dot{\omega}_i
&=
-(\mathbf{K}\boldsymbol{\theta})_i
-(\mathbf{C}\boldsymbol{\omega})_i
+ T_{\mathrm{ext},i}
\end{aligned}
\]

Implementación: `build_state_derivative` (closure; matrices \(K\), \(C\) cacheadas). Compatible con `rk4_step` vía

`lambda t, y: state_derivative(t, y, u_top(t), wob(t))`.

---

## 5. Velocidad de onda torsional

En el continuo (sin amortiguamiento):

\[
c_s = \sqrt{\frac{G}{\rho}},
\quad
T_{\mathrm{tránsito}} = \frac{L}{c_s}
\]

El test `test_torsional_wave_speed.py` aplica un escalón de \(u_{\mathrm{top}}\) sin fricción ni damping nodal y mide el arribo en \(\omega_{N-1}\). Tolerancia relativa amplia (~30%) por discretización finita; al duplicar \(N\) el error no debe empeorar.

---

## 6. Stick-Slip Severity Index (SSI)

Sobre una ventana de \(\omega_b\):

\[
\mathrm{SSI}
=
\frac{\omega_{\max}-\omega_{\min}}{2\,\omega_{\mathrm{nominal}}}
\]

| SSI | Régimen (`StickSlipRegime`) |
|-----|-----------------------------|
| \(< 0.5\) | `NORMAL` |
| \(0.5\)–\(1.0\) | `WARNING` |
| \(> 1.0\) | `CRITICAL_STICK_SLIP` |

Edge cases (ventana vacía, \(\omega_{\mathrm{nominal}}\le 0\), NaN/Inf) → `ValueError` explícito.

---

## 7. Trazabilidad fórmula → código → test

| Fórmula / invariante | Función / tipo | Test |
|----------------------|----------------|------|
| Discretización \(I_i\), \(k_i\) | `build_uniform_drillstring` | `test_state_derivative_output_dimension` |
| \(K\) tridiagonal | `build_stiffness_matrix` | `test_build_stiffness_matrix_tridiagonal_symmetry` |
| \(C\) diagonal | `build_damping_matrix` | `test_build_damping_matrix_diagonal` |
| Equilibrio rígido \(\dot{\omega}=0\) | `build_state_derivative` | `test_steady_state_torque_balance` |
| WOB → Stribeck | `bit_stribeck_parameters` | `test_bit_friction_zero_at_zero_wob` |
| \(c_s=\sqrt{G/\rho}\) | integración RK4 + FEM | `test_wave_transit_time_matches_theoretical_speed` |
| SSI y umbrales | `compute_ssi`, `classify_regime` | `test_ssi_*` |
| Sigma points Van der Merwe | `compute_sigma_points`, `compute_sigma_weights` | `test_sigma_points_*` |
| UKF predict / update | `UnscentedKalmanFilter` | `test_ukf_estimator.py` |

---

## 8. Unscented Kalman Filter (UKF)

Formulación alineada a SPEC §2.5. Código: [`sigma_points.py`](../../src/engine/kalman/sigma_points.py), [`ukf_estimator.py`](../../src/engine/kalman/ukf_estimator.py).

### 8.1 Parámetros y pesos (Van der Merwe)

\[
\lambda = \alpha^2 (n + \kappa) - n
\]

\[
\begin{aligned}
W_m^{(0)} &= \frac{\lambda}{n+\lambda},
\quad
W_c^{(0)} = \frac{\lambda}{n+\lambda} + (1 - \alpha^2 + \beta) \\
W_m^{(i)} &= W_c^{(i)} = \frac{1}{2(n+\lambda)},
\quad i = 1,\ldots,2n
\end{aligned}
\]

### 8.2 Sigma points

\[
\begin{aligned}
\mathcal{X}^{(0)} &= \hat{\mathbf{x}} \\
\mathcal{X}^{(i)} &= \hat{\mathbf{x}} + \mathbf{L}_{:,i},
\quad
\mathcal{X}^{(n+i)} &= \hat{\mathbf{x}} - \mathbf{L}_{:,i},
\quad i=1,\ldots,n
\end{aligned}
\]

con \(\mathbf{L}\mathbf{L}^{\mathsf{T}} = (n+\lambda)\,P_{\mathrm{sym}}\) y \(P_{\mathrm{sym}}=\tfrac12(P+P^{\mathsf{T}})\). Si Cholesky falla (drift numérico), se aplica jitter \(\varepsilon I\) con backoff exponencial (auditoría **A-003**).

### 8.3 Predicción

Cada sigma point se propaga un paso con `rk4_step` sobre `state_derivative(t, x, u_top, wob)`:

\[
\hat{\mathbf{x}}^- = \sum_i W_m^{(i)}\,\mathcal{X}^{(i)},
\quad
P^- = \sum_i W_c^{(i)}(\mathcal{X}^{(i)}-\hat{\mathbf{x}}^-)(\cdot)^{\mathsf{T}} + Q
\]

luego \(P^- \leftarrow \tfrac12(P^- + (P^-)^{\mathsf{T}})\).

### 8.4 Corrección

`update` reutiliza los sigma points **ya propagados** por `predict` (variante Van der Merwe; A-003). Con \(h(\mathbf{x})\):

\[
K = P_{xz}\,P_{zz}^{-1}
\quad\text{(vía ``np.linalg.solve``, no inversa explícita)}
\]

\[
\hat{\mathbf{x}} \leftarrow \hat{\mathbf{x}}^- + K(\mathbf{z}-\hat{\mathbf{z}}),
\quad
P \leftarrow P^- - K P_{zz} K^{\mathsf{T}}
\]

y se re-simetriza \(P\).

