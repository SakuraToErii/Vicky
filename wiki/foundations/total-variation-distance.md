---
title: Total Variation Distance
slug: total-variation-distance
tags:
  - probability-theory
  - information-theory
  - reinforcement-learning
aliases:
  - Total Variation Divergence
  - TV Distance
  - TV Divergence
  - Variational Distance
  - 总变差距离
  - 总变差散度
relation_extends: []
relation_uses: []
relation_compares_with: []
---

Total variation distance measures the largest probability gap that two distributions assign to the same event. For probability measures $P$ and $Q$ on the same measurable space,

$$
D_{TV}(P,Q) = \sup_A |P(A) - Q(A)|.
$$

This definition gives the strongest intuitive reading of the quantity: it is the maximum disagreement over all events. When $D_{TV}$ is small, every event receives similar probability under both distributions.

For discrete distributions $p$ and $q$, the same quantity becomes

$$
D_{TV}(p,q) = \frac{1}{2} \sum_i |p_i - q_i|.
$$

For distributions with densities, it becomes

$$
D_{TV}(p,q) = \frac{1}{2} \int |p(x) - q(x)|\,dx.
$$

The factor $\frac{1}{2}$ keeps the value in $[0,1]$, so the scale has a direct probabilistic meaning: $0$ means identical distributions, and $1$ means complete separation.

In [[trust-region-policy-optimization]], this quantity appears as the policy shift measure

$$
D^{\max}_{TV}(\pi,\tilde{\pi}) = \max_s D_{TV}(\pi(\cdot \mid s), \tilde{\pi}(\cdot \mid s)).
$$

This statewise maximum says how far the new policy moves from the old policy at the most changed state. TRPO uses it in the monotonic-improvement bound, so TV distance is the geometric quantity that controls the approximation gap between the surrogate objective and the true return.

The paper then moves from TV distance to KL divergence through

$$
D_{TV}(p,q)^2 \le D_{KL}(p \| q).
$$

This bridge matters for the algorithm design. TV distance gives the clean theoretical guarantee, and KL divergence gives a practical trust-region constraint that is easier to optimize with sampled trajectories and parameterized policies.

A compact memory hook is: total variation distance is the maximum event-level probability gap, and on discrete domains it is half of the $L_1$ gap between two probability tables.

## Relations
- External reference: [Wikipedia: Total variation distance of probability measures](https://en.wikipedia.org/wiki/Total_variation_distance_of_probability_measures)
