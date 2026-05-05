---
title: "Trust Region Policy Optimization"
slug: "trust-region-policy-optimization"
aliases:
  - "TRPO"
tags:
  - reinforcement-learning
  - policy-optimization
  - trust-region
authors:
  - John Schulman
  - Sergey Levine
  - Philipp Moritz
  - Michael I. Jordan
  - Pieter Abbeel
source_kind: paper
year: 2015
venue: "International Conference on Machine Learning"
source_path: "raw/papers/TRPO/TRPO.md"
relation_extends: []
relation_uses:
  - "[[total-variation-distance]]"
relation_compares_with: []
relation_contradicts: []
date_added: "2026-05-02"
---

## TL;DR

This paper introduces Trust Region Policy Optimization, usually abbreviated as TRPO, for reinforcement-learning policy search with large nonlinear policies such as neural networks. Its central idea is to optimize a local surrogate objective while constraining each policy update inside a KL-divergence trust region, which keeps training stable while still allowing meaningful progress.

The paper combines a monotonic-improvement argument with a practical large-scale optimizer built from conjugate gradient, Fisher information geometry, and line search. The result is a general policy optimization method that learns strong locomotion controllers in MuJoCo and competitive Atari policies from pixels with the same trust-region principle.

## Motivation

The paper starts from a practical problem that was very visible in early deep reinforcement learning: policy gradient methods offered a principled route to optimize parameterized policies, yet training often became unstable once the policy update grew too large. Gradient-free methods such as CEM and CMA sometimes behaved more robustly on hard control tasks, even though their sample efficiency scaled poorly with policy size.

The authors aim to keep the scalability of gradient-based optimization while gaining the step-to-step stability that large policy networks need. Their central idea is that policy improvement should be measured in the geometry of probability distributions, so the update rule should control how far the new policy moves from the old one in KL divergence.

## Background

The paper works in the standard infinite-horizon discounted Markov decision process setting. A stochastic policy $\pi(a \mid s)$ induces an expected discounted return $\eta(\pi)$, a state-value function $V_\pi(s)$, an action-value function $Q_\pi(s,a)$, and an advantage function $A_\pi(s,a) = Q_\pi(s,a) - V_\pi(s)$. The advantage function measures how much better an action is than the policy's own average behavior at the same state.

The key background identity says that the performance of a candidate policy $\tilde{\pi}$ can be decomposed into the performance of the current policy plus accumulated advantages under the candidate policy:

$$
\eta(\tilde{\pi}) = \eta(\pi) + \mathbb{E}_{s_0,a_0,\dots \sim \tilde{\pi}} \left[ \sum_{t=0}^{\infty} \gamma^t A_\pi(s_t, a_t) \right].
$$

This identity is powerful because it separates the old policy's value estimates from the new policy's trajectory distribution. The challenge is that the new state visitation frequencies $\rho_{\tilde{\pi}}(s)$ depend on the very policy we are trying to optimize, so direct optimization remains hard.

## Core Contribution

TRPO replaces the intractable objective with a local surrogate that freezes the state visitation distribution at the current policy:

$$
L_\pi(\tilde{\pi}) = \eta(\pi) + \sum_s \rho_\pi(s) \sum_a \tilde{\pi}(a \mid s) A_\pi(s,a).
$$

This surrogate keeps the action update flexible while holding the state distribution fixed. Around the current policy, it matches the true objective to first order, so improving $L_\pi(\tilde{\pi})$ with a small enough step also improves $\eta(\tilde{\pi})$.

The main theorem gives a monotonic-improvement style lower bound. The paper shows that policy performance stays above the surrogate objective minus a trust-region penalty:

$$
\eta(\tilde{\pi}) \ge L_\pi(\tilde{\pi}) - C \, D^{\max}_{\mathrm{KL}}(\pi,\tilde{\pi}),
\quad
C = \frac{4 \epsilon \gamma}{(1-\gamma)^2},
\quad
\epsilon = \max_{s,a} |A_\pi(s,a)|.
$$

The paper reaches this KL-based form by first expressing the bound with [[total-variation-distance]]. It defines a statewise maximum TV distance between the old and new policies, then uses $D_{TV}(p,q)^2 \le D_{KL}(p \| q)$ to move from the theoretical quantity to a practical trust-region constraint.

This result turns policy optimization into a constrained optimization problem. The algorithm seeks the policy that maximizes the surrogate objective while staying close to the current policy in KL divergence. In parameter form, with policy parameters $\theta$ and old parameters $\theta_{\mathrm{old}}$, the practical update becomes

$$
\max_\theta L_{\theta_{\mathrm{old}}}(\theta)
\quad
\text{subject to}
\quad
\overline{D}^{\rho_{\theta_{\mathrm{old}}}}_{\mathrm{KL}}(\theta_{\mathrm{old}}, \theta) \le \delta.
$$

This average-KL trust region is the practical core of TRPO. It allows steps that are large enough to make progress while still respecting the local geometry of the policy distribution.

The paper also introduces two sampling schemes. The single-path variant estimates returns from ordinary trajectories sampled under the current policy. The vine variant first collects trunk trajectories, then branches multiple short rollouts from selected states. Vine gives lower-variance local value estimates and uses common random numbers to make action comparisons sharper, while single-path applies directly in model-free settings without state resets.

## Formula Explanation

The first core formula is the policy-improvement identity:

$$
\eta(\tilde{\pi}) = \eta(\pi) + \mathbb{E}_{s_0,a_0,\dots \sim \tilde{\pi}} \left[ \sum_{t=0}^{\infty} \gamma^t A_\pi(s_t, a_t) \right].
$$

Here, $\eta(\pi)$ is the current policy's expected discounted return, $\gamma$ is the discount factor, and $A_\pi(s_t,a_t)$ measures whether action $a_t$ at state $s_t$ is better or worse than the old policy's average choice. This formula says that a new policy improves performance when it tends to collect positive old-policy advantages along its own trajectories.

The same idea can be written with discounted visitation frequencies:

$$
\eta(\tilde{\pi}) = \eta(\pi) + \sum_s \rho_{\tilde{\pi}}(s) \sum_a \tilde{\pi}(a \mid s) A_\pi(s,a).
$$

The symbol $\rho_{\tilde{\pi}}(s)$ is the discounted number of times the new policy visits state $s$. This form makes the difficulty explicit: the optimization target depends on the unknown future state distribution of the new policy itself.

TRPO resolves that difficulty with the local surrogate

$$
L_\pi(\tilde{\pi}) = \eta(\pi) + \sum_s \rho_\pi(s) \sum_a \tilde{\pi}(a \mid s) A_\pi(s,a),
$$

which replaces $\rho_{\tilde{\pi}}(s)$ with $\rho_\pi(s)$. This approximation keeps the local action-improvement signal while making the optimization manageable. The trust-region correction then protects the approximation error:

$$
\eta(\tilde{\pi}) \ge L_\pi(\tilde{\pi}) - C \, D^{\max}_{\mathrm{KL}}(\pi,\tilde{\pi}),
\quad
C = \frac{4 \epsilon \gamma}{(1-\gamma)^2}.
$$

The sample-based objective used in practice is

$$
\max_\theta
\mathbb{E}_{s \sim \rho_{\theta_{\mathrm{old}}},\, a \sim q}
\left[
\frac{\pi_\theta(a \mid s)}{q(a \mid s)}
Q_{\theta_{\mathrm{old}}}(s,a)
\right]
\quad
\text{subject to}
\quad
\mathbb{E}_{s \sim \rho_{\theta_{\mathrm{old}}}}
\left[
D_{\mathrm{KL}}(\pi_{\theta_{\mathrm{old}}}(\cdot \mid s)\,\|\,\pi_\theta(\cdot \mid s))
\right]
\le \delta.
$$

The ratio $\pi_\theta(a \mid s) / q(a \mid s)$ is an importance-sampling correction. It lets the algorithm estimate how the candidate policy would value actions even when the samples were drawn from another distribution $q$. In single-path TRPO, this sampling distribution is usually the old policy.

For vine rollouts, the paper also uses a self-normalized estimator at a chosen state $s_n$:

$$
L_n(\theta) =
\frac{
\sum_{k=1}^{K}
\frac{\pi_\theta(a_{n,k} \mid s_n)}{\pi_{\theta_{\mathrm{old}}}(a_{n,k} \mid s_n)}
\hat{Q}(s_n, a_{n,k})
}{
\sum_{k=1}^{K}
\frac{\pi_\theta(a_{n,k} \mid s_n)}{\pi_{\theta_{\mathrm{old}}}(a_{n,k} \mid s_n)}
}.
$$

This estimator aggregates several candidate actions from the same state, uses rollout returns $\hat{Q}(s_n,a_{n,k})$ as local value estimates, and reduces variance without introducing an extra baseline term.

## Experiments

The empirical study covers two very different settings: simulated robotic locomotion in MuJoCo and Atari game playing from image input. This breadth matters because TRPO is presented as a general policy-search method rather than a domain-specific controller design.

In locomotion, the paper trains policies for swimmer, hopper, and walker with neural networks and a fixed trust-region size $\delta = 0.01$. Both single-path TRPO and vine TRPO learn strong gaits across the benchmark suite. The strongest message from these experiments is that a KL-constrained update yields stable progress on underactuated, contact-rich control problems where policy updates can easily become unstable.

In Atari, the paper uses a convolutional policy with about 33,500 parameters and evaluates seven games. TRPO reaches competitive performance across the suite, including strong scores on Pong and reasonable scores on several visually diverse tasks. The paper uses the same optimization principle for locomotion and pixel-based gameplay, which supports its claim that trust-region policy updates scale across observation modalities.

## Deeper Analysis

One of the paper's most useful ideas is its view of TRPO as a unifying bridge between several older methods. A natural policy gradient step appears when the objective is linearized and the KL constraint is quadratically approximated. A standard policy gradient step appears when the constraint is Euclidean. Policy iteration appears when the surrogate is optimized over policies without a trust-region constraint. This perspective makes TRPO part of a larger design space rather than a standalone trick.

The trust region also gives a practical answer to step-size selection. A fixed penalty coefficient often couples progress to a fragile hyperparameter scale, while a KL bound directly constrains the movement of the policy distribution. The experiments support this interpretation: TRPO behaves more reliably than ablated variants that use weaker update control.

The implementation details matter as much as the theorem. The algorithm computes the search direction with conjugate gradient, represents curvature through the Fisher information matrix, and enforces the final step with line search. The vine estimator adds common random numbers to reduce variance in rollout comparisons. These choices are the reason the method remains usable with tens of thousands of parameters.

## Reflection

The paper's main insight is that reinforcement-learning policy updates benefit from geometry-aware control of policy change. TRPO turns that insight into a workable algorithm with a clear theoretical story and strong empirical support on locomotion and Atari.

Its main costs are substantial sample demand, heavy compute, and the need for simulator state resets in the vine setting. Even with those costs, TRPO established the trust-region template that strongly influenced later methods such as PPO and remains one of the clearest formulations of stable policy optimization.

## Relations
- Raw source: [[raw/papers/TRPO/TRPO.md]]
- Uses: [[total-variation-distance]] formalizes the divergence TRPO uses in its policy-improvement bound and its KL relaxation step.
- arXiv: [1502.05477](https://arxiv.org/abs/1502.05477)
- Semantic Scholar: [Trust Region Policy Optimization](https://www.semanticscholar.org/paper/449532187c94af3dd3aa55e16d2c50f7854d2199)
