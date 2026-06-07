## Physics Rules Research Problem

### 1. Variable Definitions

- **$\Delta d_v$**: Changes in total vertical deformation from InSAR
- **$\Delta b_j$**: Changes of subsurface compaction at layer $j$-th measured by multilayer compaction monitoring wells
- **$t$**: Epoch $t$ (dimensionless)
- **$\tau$**: Delay
- **$\Delta H^t$**: Changes of observed groundwater level at epoch $t$
- **$\Delta H^{(t-\tau)}$**: Changes of observed groundwater level at epoch $(t-\tau)$
- **$\alpha$**: Ratio between sum of observed subsurface compaction over InSAR

---

### 2. Model Equations

**At a single MLCW station:**

$$\alpha \cdot \Delta d_v^t = \sum_{j=1}^{N} \Delta b_j^t$$

$$\Rightarrow \Delta d_v^t = \frac{1}{\alpha} \sum_{j=1}^{N} \Delta b_j^t$$

**We have:**

$$\Delta b_j^t = (S_k)_j \cdot \Delta H_j^{t-\tau_j} \quad (\tau \ge 0)$$

Where:

- $S_k = S_{ke}$ if elastic period
- $S_k = S_{kv}$ if inelastic period

**Resulting equation:**

$$\Delta d_v^t = \frac{1}{\alpha} \sum_{j=1}^{N} (S_k)_j \Delta H_j^{t-\tau_j} \quad (\tau \ge 0)$$

With conditions:

- $S_k = S_{ke}$ (elastic)
- $S_k = S_{kv}$ (inelastic)

_Note: $(a \le S_{ke} \le b) \ ; (m \le S*{kv} \le n)$*

---

### 3. Parameters and Constraints

**Parameters to search:**

$$\alpha \ ; (S_{ke})_j \ ; (S_{kv})_j \ ; \tau_j \quad (j=1, \dots, N)$$

**Constraints:**

- $0 < \alpha < 1$
- $a \le S_{ke} \le b$
- $m \le S_{kv} \le n$
- $\tau \ge 0$

---

### 4. Optimization Objective (Simultaneous)

All parameters are solved **simultaneously** in a single minimization. The objective function combines two physical constraints — per-layer MLCW compaction and total InSAR surface deformation — into one loss:

$$
\boxed{
\min_{\alpha,\;(S_k)_j,\;\tau_j}
\underbrace{\sum_{j=1}^{N} \sum_{t} \left| (S_k)_j \cdot \Delta H_j^{t-\tau_j} - \Delta b_j^t \right|^2}_{\text{layerwise MLCW constraint}}
\;+\;
\underbrace{\sum_{t} \left| \frac{1}{\alpha} \sum_{j=1}^{N} (S_k)_j \Delta H_j^{t-\tau_j} - \Delta d_v^t \right|^2}_{\text{total InSAR constraint}}
}
$$

**Why simultaneous?** The scale factor $\alpha$ couples all layers together through the InSAR term. Solving layer-by-layer then adjusting $\alpha$ afterwards would miss the coupling — each layer's $(S_k)_j$ and the global $\alpha$ must co-adjust to satisfy both the per-layer MLCW measurements and the total surface deformation observed by InSAR.

**Subject to:**
- $0 < \alpha < 1$
- $a \le S_{ke} \le b$ , $m \le S_{kv} \le n$ (per layer)
- $\tau_j \ge 0$ (per layer)
- $S_k = S_{ke}$ during elastic periods; $S_k = S_{kv}$ during inelastic periods

---

### 5. Visual Concept Diagrams

#### Figure 1 — Physical Cross-Section: Instruments, Layers, and Measurements

```
                         ┌─────────────────┐
                         │  InSAR Satellite │
                         │   Δd_v(t)        │  ← total surface deformation
                         │   (LOS displ.)   │    at epoch t
                         └────────┬────────┘
                                  │
                                  │  line-of-sight beam
                                  ▼
    ══════════════════════════════╪══════════════════════════════════════  ground surface
                                  │
         MLCW Borehole           │              GWL Observation Well
         (compaction)            │              (hydraulic head)
         ┌───────────┐           │           ┌──────────────┐
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──Screen──────┼──────  F1 (confined aquifer 1)
         │   Δb₁(t)  │           │           │   ΔH₁(t)     │        depth ~10-40 m
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──────────────┼──────  T1 (aquitard 1)
         │   Δb₂(t)  │           │           │              │        may be single-ring
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──Screen──────┼──────  F2 (confined aquifer 2)
         │   Δb₃(t)  │           │           │   ΔH₂(t)     │        depth ~50-170 m
         │           │           │           │              │        thickest layer ~77 m
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──────────────┼──────  T2 (aquitard 2)
         │   Δb₄(t)  │           │           │              │
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──Screen──────┼──────  F3 (confined aquifer 3)
         │   Δb₅(t)  │           │           │   ΔH₃(t)     │        depth ~150-270 m
         │           │           │           │              │
         │           │           │           │              │
    ─────┼──Ring─────┼───────────┼───────────┼──────────────┼──────  F4 (confined aquifer 4)
         │   Δb₆(t)  │           │           │              │        depth ~260-340 m
         │           │           │           │              │
         └───────────┘           │           └──────────────┘
                                 │
    ══════════════════════════════╪══════════════════════════════════════  bedrock (impermeable)
                                 │

    Legend:
      ○ = magnetic ring (MLCW)     ┌─Screen──┐ = GWL well screen interval
      Δbⱼ = compaction of layer j   ΔHⱼ = groundwater level change in layer j
```

---

#### Figure 2 — Signal Flow: From GWL ΔH to InSAR Δd_v

```
    Layer j                 GWL Well                  MLCW Ring Pair
    ─────────             ────────────              ──────────────────
                           
                           ΔHⱼ(t)                        Δbⱼ(t)
                             │                              ▲
                             │    ┌─────────────────────────┘
                             │    │   Δbⱼ(t) = S_kⱼ · ΔHⱼ(t − τⱼ)
                             │    │
                             ▼    │
                    ┌─────────────────────┐
                    │  Two-Regime Switch   │
                    │                     │
                    │  if elastic:        │
                    │    S_k = S_ke       │
                    │  if inelastic:      │
                    │    S_k = S_kv       │
                    └─────────────────────┘
                             │
                             │  applies to each layer
                             ▼

       ┌─────────────────────────────────────────────────────┐
       │              Σ over all N layers                     │
       │                                                     │
       │  Σⱼ Δbⱼ(t) = Σⱼ (S_k)ⱼ · ΔHⱼ(t − τⱼ)              │
       │                                                     │
       └────────────────────────┬────────────────────────────┘
                                │
                                │  scaled by 1/α
                                ▼
                    ┌───────────────────────┐
                    │                       │
                    │  Δd_v(t) = (1/α) · Σⱼ Δbⱼ(t)  │
                    │                       │
                    └───────────────────────┘
                                │
                                │  compared to observed InSAR
                                ▼
                         ┌──────────┐
                         │  InSAR   │
                         │  Δd_v(t) │  ← measured from satellite
                         └──────────┘
```

---

#### Figure 3 — Simultaneous Optimization: All Parameters in One Pass

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║              SINGLE SIMULTANEOUS OPTIMIZATION                        ║
    ║                                                                      ║
    ║  Unknowns:  α , (S_ke)ⱼ , (S_kv)ⱼ , τⱼ   for j = 1..N              ║
    ║                                                                      ║
    ║  ┌─────────────────────────────────────────────────────────────┐    ║
    ║  │                    COMBINED OBJECTIVE                         │    ║
    ║  │                                                               │    ║
    ║  │   Layerwise term               Total InSAR term               │    ║
    ║  │   ┌─────────────────┐          ┌─────────────────────┐        │    ║
    ║  │   │  Σⱼ Σₜ           │          │  Σₜ                   │        │    ║
    ║  │   │  |S_kⱼ·ΔHⱼ(t−τⱼ) │   +      │  |(1/α)·Σⱼ Δbⱼ − Δd_v|²  │        │    ║
    ║  │   │  − Δbⱼ(t)|²      │          │                       │        │    ║
    ║  │   └─────────────────┘          └─────────────────────┘        │    ║
    ║  │          ↑                              ↑                      │    ║
    ║  │    MLCW per-layer               InSAR total surface            │    ║
    ║  │    compaction data               deformation data               │    ║
    ║  └─────────────────────────────────────────────────────────────┘    ║
    ║                                │                                     ║
    ║                                ▼                                     ║
    ║  ┌──────────────────────────────────────────────────────────────┐   ║
    ║  │  All parameters co-adjusted in one minimization:              │   ║
    ║  │                                                               │   ║
    ║  │    α  ←──→  (S_k)₁  ←──→  τ₁                                  │   ║
    ║  │    │         │            │                                    │   ║
    ║  │    │    ┌────┘       ┌────┘                                    │   ║
    ║  │    │    │            │                                         │   ║
    ║  │    ├────┼────────────┼──→  (S_k)₂  ←──→  τ₂                   │   ║
    ║  │    │    │            │      │          │                        │   ║
    ║  │    │    │            │      │          │                        │   ║
    ║  │    │    └────────────┼──────┼──────────┼──→  ...              │   ║
    ║  │    │                 │      │          │                        │   ║
    ║  │    └─────────────────┼──────┼──────────┼──→  (S_k)ₙ ←──→ τₙ  │   ║
    ║  │                      │      │          │                        │   ║
    ║  └──────────────────────────────────────────────────────────────┘   ║
    ║                                                                      ║
    ║  α couples all layers: cannot be separated into stages.              ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

---

### 6. Summary of Unknown Parameters

| Symbol | Description | Layer-specific? | Range |
|--------|-------------|:---:|-------|
| $(S_{ke})_j$ | Elastic skeletal storage coefficient | Yes (j=1..N) | $a \le S_{ke} \le b$ |
| $(S_{kv})_j$ | Inelastic skeletal storage coefficient | Yes (j=1..N) | $m \le S_{kv} \le n$ |
| $\tau_j$ | GWL-to-compaction time delay | Yes (j=1..N) | $\tau \ge 0$ |
| $\alpha$ | Sum(MLCW) / InSAR scale factor | No (global) | $0 < \alpha < 1$ |

**Total unknowns:** $3N + 1$ parameters ($N$ = number of layers, typically 6).
**All solved simultaneously** in a single combined objective (Section 4).
