# Q-SENTINEL Security Analysis

## 1. Adversary Model

This security bound holds against an **individual-measurement adversary without quantum memory**.

**Granted to the adversary:**
- Intercept and modify quantum channel states
- Intercept and modify the classical correction channel
- Submit arbitrary API requests
- Hold valid credentials for its own identity (`mallory`)
- Write access to the evidence database file
- Unlimited adaptive queries (subject to rate limits)

**Withheld from the adversary:**
- The signer's private key elements
- Quantum memory
- Coherent or collective attacks across positions
- Access to the keyvault or ledger service networks/processes

## 2. Information-Theoretic Security Statement

The quantum unforgeability layer is information-theoretically secure **conditional on** (a) uniformly random single-use keys, (b) single-copy non-orthogonal states, and (c) the individual-measurement adversary model. 

The classical transport authentication layer is post-quantum computationally secure (Module-Lattice DSA, FIPS 204).

## 3. Protocol Key Material

For each signing session, independent key elements are generated using a CSPRNG:
```
For i ∈ [0, L), b ∈ {0, 1}:
    k_i^b  ←  CSPRNG
    s_i^b  =  state_map(k_i^b)
```
Where `state_map` draws from the six-state ensemble: `{|0⟩, |1⟩, |+⟩, |−⟩, |i⟩, |−i⟩}`.
These elements are independent of the message and single-use.

## 4. Forgery Probability Bound

The optimal adversary success probability for the six-state ensemble against an individual-measurement adversary is $p_{opt} = (1 + 1/\sqrt{3}) / 2 \approx 0.7887$.

Over the matched subset $n \approx L/3$, the number of mismatches follows a binomial distribution. The forgery probability is bounded by:

$$P_{forge}(L, s_a) = P(\text{Binomial}(n, 1 - p_{opt}) \leq \lfloor s_a \cdot n \rfloor)$$

This decays **exponentially** in $L$.

## 5. Non-Repudiation and Dispute Resolution

The protocol achieves non-repudiation via dual thresholds $s_a < s_v$:
- **Verifier 1** accepts if the mismatch rate $\hat{m} < s_a$
- **Verifier 2** accepts if the mismatch rate $\hat{m} < s_v$

Transferability is guaranteed because if Verifier 1 accepts, the expected mismatch rate at Verifier 2 remains below $s_v$.

**Dispute Protocol:**
1. **Repudiation:** Signer denies signing. Verifier's records show agreement with the signer's revealed keys at a rate higher than any adversary could achieve ($\hat{m} < s_v$). The signature is upheld.
2. **Framing:** Verifier claims a forged signature. The records show random outcomes, failing to corroborate the claim.
3. **Split Verdict:** If Verifier 1 accepts but Verifier 2 rejects, Verifier 2's stricter bound takes precedence. The ledger records the dispute resolution.
