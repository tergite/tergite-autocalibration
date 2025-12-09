---
title: Two Qubit Clifford Randomized Benchmarking
---

# Two qubit Clifford group

The two-qubit Clifford group is generated from single-qubit unitaries and the controlled-NOT (CNOT) gate. When implementing the protocol, it's crucial to use a Clifford decomposition that minimizes the number of two-qubit gates, as these generally have lower fidelities than single-qubit gates.

As in the single qubit case, the *exponential decay* should be fit to

\begin{equation}
F(m)= Ap^m + B \label{eq:survival_rate}
\end{equation}

where $m$ is the number of Cliffords in the sequence, and $A$ and $B$ are parameters related to state preparation and measurement, and $1-p$ is the depolarization rate.

The two-qubit Clifford group can be divided into **four classes** [^corcolesProcessVerificationTwoqubit2013]:  

1. The **Single-qubit Clifford class** that consists of 576 elements ($24^2$) and represents all single-qubit Clifford operations:

```text
(q0) --C1--

(q1) --C1--
```

2. The **CNOT-class** that has 5184 elements ($24^2\times 3^2$) and contains all combinations of the following sequence:

```text
(q0)  --C1--•--S1--
            | 
(q1)  --C1--⊕--S1-- 
```

3. The **ISWAP-class** The **third class** also has 5184 elements and contains all combinations of the following sequence:

```text
(q0)  --C1--*--S1--
            |    
(q1)  --C1--*--S1-- 
```

4. **SWAP-class**. The **fourth class** is the *SWAP-class* and consists of all 576 ($24^2$) combinations of the following sequence:

```text
(q0)  --C1--x--
            |  
(q1)  --C1--x--  
```

Therefore, there are in total *11 520* elements in the two-qubit Clifford group.

## Gate Decomposition

The decomposition of the two-qubit Clifford group above is the *optimal* in terms of the number of CNOTs. Since an iSWAP requires two CNOTs and a SWAP requires three, the *average number of CNOTs per Clifford operation* is **1.5**. The same holds if we use CZ instead of CNOT as the building block, since the CNOT can be decomposed as a CZ with two Hadamards. The number of single-qubit gates depends on how the single-qubit Cliffords are implemented.

Below follows the *decomposition* of the two-qubit gates in terms of the CZ-gate and single-qubit -gates:

1. **CNOT to CZ**  

```text
(q0)  --C1--•--S1--      --C1--•--S1------
            |        ->        |
(q1)  --C1--⊕--S1--      --C1--•--S1^Y90--
```

2. **iSWAP to CZ**  

```text
(q0)  --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
            |       ->        |        |
(q1)  --C1--*--S1--     --C1--•--mY90--•--S1^X90--
```

3. **SWAP to CZ**  

```text
(q0)  --C1--x--     --C1--•-mY90--•--Y90--•-------
            |   ->        |       |       |
(q1)  --C1--x--     --C1--•--Y90--•-mY90--•--Y90--
```

### Interleaved Clifford Randomized Benchmarking

*Interleaved Clifford Randomized Benchmarking* allows estimation of the error associated with an individual Clifford gate. The core idea is to perform two benchmarking experiments: one following the standard Clifford Randomized Benchmarking (RB) method and one with the target Clifford gate interleaved [^lallReviewCollectionMetrics2025].

If the standard RB sequence is:

$$
C_1C_2\ldots C_m C_\mathrm{inverse},
$$

where each $C$ is a Clifford gate, then the interleaved RB sequence introduces the Clifford gate $C_\mathrm{target}$ spaced in between the Clifford gates:

$$
C_1C_\mathrm{target}C_2C_\mathrm{target}\ldots C_mC_\mathrm{target}C'_\mathrm{inverse}
$$

where $C_\mathrm{target}$ is the gate being characterized and must also belong to the Clifford group, and $C'_\mathrm{inverse}$ is the final inverting gate that must be updated to invert the full gate sequence including $C_\mathrm{target}$.

The error of $C_\mathrm{target}$ is thus determined by comparing the decay rates Eq. $\eqref{eq:survival_rate}$ of the standard Clifford RB and the interleaved Clifford RB experiments.

If the fitted decay parameters from the standard RB and the interleaved RB are denoted by $p$ and $p_\mathrm{interleaved}$ respectively. Then, the interleaved RB gate error for $C_\mathrm{target}$ is found using

$$
r_{C_\mathrm{target}}=\frac{(d-1)(1-\frac{p_\mathrm{interleaved}}{p})}{d}
$$

where $d$ is the dimension of the system (e.g., $d=2^n$ for an $n$-qubit system).

[^corcolesProcessVerificationTwoqubit2013]: A. D. Córcoles, J. M. Gambetta, J. M. Chow, J. A. Smolin, M. Ware, J. D. Strand, B. L. T. Plourde & M. Steffen. Process verification of two-qubit quantum gates by randomized benchmarking. [Physical Review A, 87, 030301(R) (2013)](https://doi.org/10.1103/PhysRevA.87.030301). 
[^lallReviewCollectionMetrics2025]: Lall, D., Agarwal, A., Zhang, W., Lindoy, L., Lindström, T., Webster, S., Hall, S., Chancellor, N., Wallden, P., Garcia-Patrón, R., Kashefi, E., Kendon, V., Pritchard, J., Rossi, A., Datta, A., Kapourniotis, T., Georgopoulos, K., & Rungger, I. (2025). A Review and Collection of Metrics and Benchmarks for Quantum Computers: definitions, methodologies and software. [arXiv:2502.06717](https://arxiv.org/abs/2502.06717)