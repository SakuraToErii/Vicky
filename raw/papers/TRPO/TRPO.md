# Trust Region Policy Optimization

**Authors:** John Schulman, Sergey Levine, Philipp Moritz, Michael I. Jordan, Pieter Abbeel

**Affiliations:** University of California, Berkeley, Department of Electrical Engineering and Computer Sciences

## Abstract

We describe an iterative procedure for optimizing policies, with guaranteed monotonic improvement. By making several approximations to the theoretically-justified procedure, we develop a practical algorithm, called Trust Region Policy Optimization (TRPO). This algorithm is similar to natural policy gradient methods and is effective for optimizing large nonlinear policies such as neural networks. Our experiments demonstrate its robust performance on a wide variety of tasks: learning simulated robotic swimming, hopping, and walking gaits; and playing Atari games using images of the screen as input. Despite its approximations that deviate from the theory, TRPO tends to give monotonic improvement, with little tuning of hyperparameters.

## 1. Introduction

Most algorithms for policy optimization can be classified into three broad categories: (1) policy iteration methods, which alternate between estimating the value function under the current policy and improving the policy [1]; (2) policy gradient methods, which use an estimator of the gradient of the expected return (total reward) obtained from sample trajectories [2] (and which, as we later discuss, have a close connection to policy iteration); and (3) derivative-free optimization methods, such as the cross-entropy method (CEM) and covariance matrix adaptation (CMA), which treat the return as a black box function to be optimized in terms of the policy parameters [3].

General derivative-free stochastic optimization methods such as CEM and CMA are preferred on many problems, because they achieve good results while being simple to understand and implement. For example, while Tetris is a classic benchmark problem for approximate dynamic programming (ADP) methods, stochastic optimization methods are difficult to beat on this task [5]. For continuous control problems, methods like CMA have been successful at learning control policies for challenging tasks like locomotion when provided with hand-engineered policy classes with low-dimensional parameterizations [6]. The inability of ADP and gradient-based methods to consistently beat gradient-free random search is unsatisfying, since gradient-based optimization algorithms enjoy much better sample complexity guarantees than gradient-free methods [7]. Continuous gradient-based optimization has been very successful at learning function approximators for supervised learning tasks with huge numbers of parameters, and extending their success to reinforcement learning would allow for efficient training of complex and powerful policies.

In this article, we first prove that minimizing a certain surrogate objective function guarantees policy improvement with non-trivial step sizes. Then we make a series of approximations to the theoretically-justified algorithm, yielding a practical algorithm, which we call trust region policy optimization (TRPO). We describe two variants of this algorithm: first, the *single-path* method, which can be applied in the model-free setting; second, the *vine* method, which requires the system to be restored to particular states, which is typically only possible in simulation. These algorithms are scalable and can optimize nonlinear policies with tens of thousands of parameters, which have previously posed a major challenge for model-free policy search [10]. In our experiments, we show that the same TRPO methods can learn complex policies for swimming, hopping, and walking, as well as playing Atari games directly from raw images.

## 2. Preliminaries

Consider an infinite-horizon discounted Markov decision process (MDP), defined by the tuple $(\mathcal{S}, \mathcal{A}, P, r, \rho_0, \gamma)$, where $\mathcal{S}$ is a finite set of states, $\mathcal{A}$ is a finite set of actions, $P: \mathcal{S} \times \mathcal{A} \times \mathcal{S} \rightarrow \mathbb{R}$ is the transition probability distribution, $r: \mathcal{S} \rightarrow \mathbb{R}$ is the reward function, $\rho_0: \mathcal{S} \rightarrow \mathbb{R}$ is the distribution of the initial state $s_0$, and $\gamma \in (0,1)$ is the discount factor.

Let $\pi$ denote a stochastic policy $\pi: \mathcal{S} \times \mathcal{A} \rightarrow [0,1]$, and let $\eta(\pi)$ denote its expected discounted reward:

$$
\begin{align*}
&\eta(\pi) = \mathbb{E}_{s_0,a_0,\dots}\left[\sum_{t=0}^{\infty} \gamma^t r(s_t)\right], \text{ where}\\
&s_0 \sim \rho_0(s_0),\ a_{t} \sim \pi(a_t |  s_t), \ s_{t+1} \sim P(s_{t+1} |  s_t, a_t).
\end{align*}
$$

We will use the following standard definitions of the state-action value function $Q_{\pi}$, the value function $V_{\pi}$, and the advantage function $A_{\pi}$:

$$
\begin{align*}
&Q_{\pi}(s_t, a_t) = \mathbb{E}_{s_{t+1},a_{t+1},\dots}\left[\sum_{l=0}^{\infty} \gamma^{l} r(s_{t+l})\right], \\
&V_{\pi}(s_t) =\ \mathbb{E}_{a_t,s_{t+1},\dots}\left[\sum_{l=0}^{\infty} \gamma^{l} r(s_{t+l})\right],\\
&A_{\pi}(s,a) =\  Q_{\pi}(s,a) - V_{\pi}(s), \text{ where} \\
&\quad a_{t} \sim \pi(a_t |  s_t), s_{t+1} \sim P(s_{t+1} |  s_t, a_t) \text{\ for }t\ge 0.
\end{align*}
$$

The following useful identity expresses the expected return of another policy $\tilde{\pi}$ in terms of the advantage over $\pi$, accumulated over timesteps (see [11] or Appendix A for proof):

$$
\begin{align}

&\eta(\tilde{\pi}) = \eta(\pi) +  \mathbb{E}_{s_0, a_0, \dots \sim \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t A_{\pi}(s_t, a_t)\right] \tag{1}
\end{align}
$$

where the notation $\mathbb{E}_{s_0, a_0, \dots \sim \tilde{\pi}}\left[\dots\right]$ indicates that actions are sampled $a_t \sim \tilde{\pi}(\cdot | s_t)$. Let $\rho_{\pi}$ be the (unnormalized) discounted visitation frequencies

$$
\begin{align}
\rho_{\pi}(s) \!=\! P(s_0=s) \!+\! \gamma P(s_1= s) \!+\! \gamma^2 P(s_2 = s) \!+\! \dots,
\end{align}
$$

where $s_0 \sim \rho_0$ and the actions are chosen according to $\pi$. We can rewrite Equation (1) with a sum over states instead of timesteps:

$$
\begin{align}

\eta(\tilde{\pi})
&= \eta(\pi) +  \sum_{t=0}^{\infty} \sum_s P(s_t = s | \tilde{\pi})\sum_a \tilde{\pi}(a | s) \gamma^t A_{\pi}(s, a) \\
&= \eta(\pi) +  \sum_s  \sum_{t=0}^{\infty} \gamma^t P(s_t = s | \tilde{\pi})\sum_a \tilde{\pi}(a | s) A_{\pi}(s, a) \\
&= \eta(\pi) + \sum_s \rho_{\tilde{\pi}}(s) \sum_a \tilde{\pi}(a |  s) A_{\pi}(s,a). \tag{2}
\end{align}
$$

This equation implies that any policy update $\pi \rightarrow \tilde{\pi}$ that has a nonnegative expected advantage at *every* state $s$, i.e., $\sum_a \tilde{\pi}(a| s) A_{\pi}(s,a) \ge 0$, is guaranteed to increase the policy performance $\eta$, or leave it constant in the case that the expected advantage is zero everywhere. This implies the classic result that the update performed by exact policy iteration, which uses the deterministic policy $\tilde{\pi}(s) = \operatorname*{arg\,max}_a A_{\pi}(s, a)$, improves the policy if there is at least one state-action pair with a positive advantage value and nonzero state visitation probability, otherwise the algorithm has converged to the optimal policy. However, in the approximate setting, it will typically be unavoidable, due to estimation and approximation error, that there will be some states $s$ for which the expected advantage is negative, that is, $\sum_a \tilde{\pi}(a |  s) A_{\pi}(s,a) < 0$. The complex dependency of $\rho_{\tilde{\pi}}(s)$ on $\tilde{\pi}$ makes Equation (2) difficult to optimize directly. Instead, we introduce the following local approximation to $\eta$:

$$
\begin{align}

L_{\pi}(\tilde{\pi}) = \eta(\pi) + \sum_s \rho_{\color{red} \pi}(s) \sum_a \tilde{\pi}(a |  s) A_{\pi}(s,a). \tag{3}
\end{align}
$$

Note that $L_{\pi}$ uses the visitation frequency $\rho_{\pi}$ rather than $\rho_{\tilde{\pi}}$, ignoring changes in state visitation density due to changes in the policy. However, if we have a parameterized policy $\pi_{\theta}$, where $\pi_{\theta}(a| s)$ is a differentiable function of the parameter vector $\theta$, then $L_{\pi}$ matches $\eta$ to first order (see [11]).[^1] That is, for any parameter value $\theta_0$,

$$
\begin{align}

L_{\pi_{\theta_0}}(\pi_{\theta_0}) &= \eta(\pi_{\theta_0}), \\
\nabla_{\theta} L_{\pi_{\theta_0}}(\pi_{\theta})\big\rvert_{\theta=\theta_0} &= \nabla_{\theta} \eta(\pi_{\theta})\big\rvert_{\theta=\theta_0}. \tag{4}
\end{align}
$$

Equation (4) implies that a sufficiently small step $\pi_{\theta_0} \rightarrow \tilde{\pi}$ that improves $L_{\pi_{\theta_{\mathrm{old}}}}$ will also improve $\eta$, but does not give us any guidance on how big of a step to take.

To address this issue, [11] proposed a policy updating scheme called conservative policy iteration, for which they could provide explicit lower bounds on the improvement of $\eta$. To define the conservative policy iteration update, let $\pi_{\mathrm{old}}$ denote the current policy, and let $\pi' = \operatorname*{arg\,max}_{\pi'} L_{\pi_{\mathrm{old}}}(\pi')$. The new policy $\pi_{\mathrm{new}}$ was defined to be the following mixture:

$$
\begin{align}

\pi_{\mathrm{new}}(a| s) = (1-\alpha) \pi_{\mathrm{old}}(a| s) + \alpha \pi'(a| s). \tag{5}
\end{align}
$$

Kakade and Langford derived the following lower bound:

$$
\begin{align}

\eta(\pi_{\mathrm{new}})
&\!\ge\! L_{\pi_{\mathrm{old}}}(\pi_{\mathrm{new}}) - \frac{2 \epsilon \gamma  }{(1-\gamma)^2} \alpha^2 \\
&\text{ where } \epsilon = \max_s | \mathbb{E}_{a \sim \pi'(a| s)}\left[A_{\pi}(s,a) \right]|. \tag{6}
\end{align}
$$

(We have modified it to make it slightly weaker but simpler.) Note, however, that so far this bound only applies to mixture policies generated by Equation (5). This policy class is unwieldy and restrictive in practice, and it is desirable for a practical policy update scheme to be applicable to all general stochastic policy classes.

## 3. Monotonic Improvement Guarantee for General Stochastic Policies

Equation (6), which applies to conservative policy iteration, implies that a policy update that improves the right-hand side is guaranteed to improve the true performance $\eta$. **Our principal theoretical result is that the policy improvement bound in Equation (6) can be extended to general stochastic policies, rather than just mixture polices, by replacing $\alpha$ with a distance measure between $\pi$ and $\tilde{\pi}$, and changing the constant $\epsilon$ appropriately**. Since mixture policies are rarely used in practice, this result is crucial for extending the improvement guarantee to practical problems. The particular distance measure we use is the *total variation divergence*, which is defined by $D_{TV}(p \ \| \ q) = \frac{1}{2} \sum_i |p_i - q_i|$ for discrete probability distributions $p,q$.[^2] Define $D^{\rm max}_{\rm TV}(\pi,\tilde{\pi})$ as

$$
\begin{align}

D^{\rm max}_{\rm TV}(\pi,\tilde{\pi}) = \max_s D_{TV}(\pi(\cdot |  s) \ \| \ \tilde{\pi}(\cdot |  s) ). \tag{7}
\end{align}
$$

**Theorem 1**. Let $\alpha = D^{\rm max}_{\rm TV}(\pi_{\mathrm{old}},\pi_{\mathrm{new}})$. Then the following bound holds:

$$
\begin{align}

&\eta(\pi_{\mathrm{new}}) \ge L_{\pi_{\mathrm{old}}}(\pi_{\mathrm{new}}) - \frac{4 \epsilon \gamma  }{(1-\gamma)^2} \alpha^2 \\
&\quad\text{ where } \epsilon = \max_{s,a}{|A_{\pi}(s,a)|} \tag{8}
\end{align}
$$

We provide two proofs in the appendix. The first proof extends Kakade and Langford's result using the fact that the random variables from two distributions with total variation divergence less than $\alpha$ can be coupled, so that they are equal with probability $1-\alpha$. The second proof uses perturbation theory.

Next, we note the following relationship between the total variation divergence and the KL divergence ([12], Ch. 3): $D_{TV}(p \ \| \ q)^2 \le D_{\rm KL}(p \ \| \ q)$. Let ${D^{\rm max}_{\rm KL}}(\pi,\tilde{\pi}) = \max_s D_{\rm KL}(\pi(\cdot |  s) \ \| \ \tilde{\pi}(\cdot |  s))$. The following bound then follows directly from Theorem 1:

$$
\begin{align}

&\eta(\tilde{\pi})  \ge L_{\pi}(\tilde{\pi}) - C {D^{\rm max}_{\rm KL}}(\pi,\tilde{\pi}), \\
&\qquad \text{ where } C = \frac{4 \epsilon \gamma}{(1-\gamma)^2}. \tag{9}
\end{align}
$$

Algorithm 1 describes an approximate policy iteration scheme based on the policy improvement bound in Equation (9). Note that for now, we assume exact evaluation of the advantage values $A_{\pi}$.

**Algorithm.** Policy iteration algorithm guaranteeing non-decreasing expected return $\eta$

- Initialize $\pi_0$.

- For $i=0,1,2,\dots$ until convergence:

  - Compute all advantage values $A_{\pi_i}(s,a)$.

  - Solve the constrained optimization problem

    $$
    \begin{align*}
    \qquad\pi_{i+1} &=\operatorname*{arg\,max}_{\pi} \left[ L_{\pi_i}(\pi) - C {D^{\rm max}_{\rm KL}}(\pi_i,\pi) \right]  \\
    &\!\!\!\!\!\text{ where }C=4\epsilon\gamma/(1-\gamma)^2\\
    &\!\!\!\!\!\text{ and } L_{\pi_i}(\pi) \!=\! \eta(\pi_i) \!+\! \sum_s \rho_{\pi_i}\!(s)\! \sum_a \! \pi(a |  s) A_{\pi_i}(s,a)
    \end{align*}
    $$

- End For.

It follows from Equation (9) that Algorithm 1 is guaranteed to generate a monotonically improving sequence of policies $\eta(\pi_0) \le \eta(\pi_1) \le \eta(\pi_2) \le \dots$. To see this, let $M_i(\pi) = L_{\pi_i}(\pi) - C {D^{\rm max}_{\rm KL}}(\pi_i, \pi)$. Then

$$
\begin{align}

&\eta(\pi_{i+1})
\ge  M_i(\pi_{i+1}) \text{ by Equation~(9)} \\
&\eta(\pi_{i})
=  M_i(\pi_i), \text{ therefore,} \\
&\eta(\pi_{i+1}) - \eta(\pi_i) \ge M_i(\pi_{i+1}) - M(\pi_i). \tag{10}
\end{align}
$$

Thus, by maximizing $M_i$ at each iteration, we guarantee that the true objective $\eta$ is non-decreasing. This algorithm is a type of minorization-maximization (MM) algorithm [13], which is a class of methods that also includes expectation maximization. In the terminology of MM algorithms, $M_i$ is the surrogate function that minorizes $\eta$ with equality at $\pi_i$. This algorithm is also reminiscent of proximal gradient methods and mirror descent.

*Trust region policy optimization*, which we propose in the following section, is an approximation to Algorithm 1, which uses a constraint on the KL divergence rather than a penalty to robustly allow large updates.

## 4. Optimization of Parameterized Policies

In the previous section, we considered the policy optimization problem independently of the parameterization of $\pi$ and under the assumption that the policy can be evaluated at all states. We now describe how to derive a practical algorithm from these theoretical foundations, under finite sample counts and arbitrary parameterizations.

Since we consider parameterized policies $\pi_{\theta}(a |  s)$ with parameter vector $\theta$, we will overload our previous notation to use functions of $\theta$ rather than $\pi$, e.g. $\eta(\theta)  := \eta(\pi_{\theta})$, $L_{\theta}(\tilde{\theta}) := L_{\pi_{\theta}}(\pi_{\tilde{\theta}})$, and $D_{\rm KL}(\theta \ \| \ \tilde{\theta}) := D_{\rm KL}(\pi_{\theta} \ \| \ \pi_{\tilde{\theta}})$. We will use $\theta_{\mathrm{old}}$ to denote the previous policy parameters that we want to improve upon.

The preceding section showed that $\eta(\theta) \ge L_{\theta_{\mathrm{old}}}(\theta)-C {D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}}, \theta)$, with equality at $\theta=\theta_{\mathrm{old}}$. Thus, by performing the following maximization, we are guaranteed to improve the true objective $\eta$:

$$
\begin{align*}
\operatorname*{maximize}_{\theta} \left[L_{\theta_{\mathrm{old}}}(\theta) - C {D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}}, \theta) \right].
\end{align*}
$$

In practice, if we used the penalty coefficient $C$ recommended by the theory above, the step sizes would be very small. One way to take larger steps in a robust way is to use a constraint on the KL divergence between the new policy and the old policy, i.e., a trust region constraint:

$$
\begin{align}

&\operatorname*{maximize}_{\theta}  L_{\theta_{\mathrm{old}}}(\theta) \tag{11} \\
&\text{\ \  subject to }  {D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}},\theta) \le \delta.
\end{align}
$$

This problem imposes a constraint that the KL divergence is bounded at every point in the state space. While it is motivated by the theory, this problem is impractical to solve due to the large number of constraints. Instead, we can use a heuristic approximation which considers the average KL divergence:

$$
\begin{align*}
{\overline D_{\rm KL}^{\rho}}(\theta_1,\theta_2) := \mathbb{E}_{s \sim \rho}\left[D_{\rm KL}(\pi_{\theta_1}(\cdot |  s) \ \| \ \pi_{\theta_2}(\cdot| s))\right].
\end{align*}
$$

We therefore propose solving the following optimization problem to generate a policy update:

$$
\begin{align}

&\operatorname*{maximize}_{\theta}  L_{\theta_{\mathrm{old}}}(\theta) \tag{12} \\
&\text{\ \  subject to }  {\overline D_{\rm KL}^{\rho_{\theta_{\mathrm{old}}}}}(\theta_{\mathrm{old}},\theta) \le \delta.
\end{align}
$$

Similar policy updates have been proposed in prior work [18, 19, 20], and we compare our approach to prior methods in Section 7 and in the experiments in Section 8. Our experiments also show that this type of constrained update has similar empirical performance to the maximum KL divergence constraint in Equation (11).

## 5. Sample-Based Estimation of the Objective and Constraint

The previous section proposed a constrained optimization problem on the policy parameters (Equation (12)), which optimizes an estimate of the expected total reward $\eta$ subject to a constraint on the change in the policy at each update. This section describes how the objective and constraint functions can be approximated using Monte Carlo simulation.

We seek to solve the following optimization problem, obtained by expanding $L_{\theta_{\mathrm{old}}}$ in Equation (12):

$$
\begin{align}

\operatorname*{maximize}_{\theta}
\sum_s &\rho_{\theta_{\mathrm{old}}}(s) \sum_a \pi_{\theta}(a| s) A_{\theta_{\mathrm{old}}}(s,a) \\
&\text{\ \  subject to }
{\overline D_{\rm KL}^{\rho_{\theta_{\mathrm{old}}}}}(\theta_{\mathrm{old}},\theta) \le \delta. \tag{13}
\end{align}
$$

We first replace $\sum_s \rho_{\theta_{\mathrm{old}}}(s) \left[\dots\right]$ in the objective by the expectation $\frac{1}{1-\gamma}\mathbb{E}_{s \sim \rho_{\theta_{\mathrm{old}}}}\left[\dots\right]$. Next, we replace the advantage values $A_{\theta_{\mathrm{old}}}$ by the $Q$-values $Q_{\theta_{\mathrm{old}}}$ in Equation (13), which only changes the objective by a constant. Last, we replace the sum over the actions by an importance sampling estimator. Using $q$ to denote the sampling distribution, the contribution of a single $s_n$ to the loss function is

$$
\begin{align}
\sum_a \pi_{\theta}(a |  s_n) A_{\theta_{\mathrm{old}}}(s_n,a)
=
\mathbb{E}_{a \sim q}\left[\frac{\pi_{\theta}(a |  s_n)}{q(a |  s_n)}A_{\theta_{\mathrm{old}}}(s_n,a) \right].

\end{align}
$$

Our optimization problem in Equation (13) is exactly equivalent to the following one, written in terms of expectations:

$$
\begin{align}

&\operatorname*{maximize}_{\theta} \mathbb{E}_{s \sim \rho_{\theta_{\mathrm{old}}}, a \sim q}\left[ \frac{\pi_{\theta}(a| s)}{q(a| s)} Q_{\theta_{\mathrm{old}}}(s,a)\right] \tag{14} \\
&\text{\ \  subject to }
\mathbb{E}_{s \sim \rho_{\theta_{\mathrm{old}}}}\left[D_{\rm KL}(\pi_{\theta_{\mathrm{old}}}(\cdot |  s) \ \| \ \pi_{\theta}(\cdot| s))\right]
\le \delta.
\end{align}
$$

All that remains is to replace the expectations by sample averages and replace the $Q$ value by an empirical estimate. The following sections describe two different schemes for performing this estimation.

The first sampling scheme, which we call *single path*, is the one that is typically used for policy gradient estimation [21], and is based on sampling individual trajectories. The second scheme, which we call *vine*, involves constructing a rollout set and then performing multiple actions from each state in the rollout set. This method has mostly been explored in the context of policy iteration methods [22, 5].

### 5.1. Single Path

In this estimation procedure, we collect a sequence of states by sampling $s_0 \sim \rho_0$ and then simulating the policy $\pi_{\theta_{\mathrm{old}}}$ for some number of timesteps to generate a trajectory $s_0, a_0, s_1, a_1, \dots, s_{T-1},a_{T-1},s_T$. Hence, $q(a | s) = \pi_{\theta_{\mathrm{old}}}(a | s)$. $Q_{\theta_{\mathrm{old}}}(s,a)$ is computed at each state-action pair $(s_t,a_t)$ by taking the discounted sum of future rewards along the trajectory.

### 5.2. Vine

<p><img src="assets/singlepath.png" style="height: 5cm;" />
<img src="assets/vines.png" style="height: 5cm;" /></p>

Figure: Left: illustration of single path procedure. Here, we generate a set of trajectories via simulation of the policy and incorporate all state-action pairs ($s_n,a_n$) into the objective. Right: illustration of vine procedure. We generate a set of "trunk" trajectories, and then generate "branch" rollouts from a subset of the reached states. For each of these states $s_n$, we perform multiple actions ($a_1$ and $a_2$ here) and perform a rollout after each action, using common random numbers (CRN) to reduce the variance.

In this estimation procedure, we first sample $s_0 \sim \rho_0$ and simulate the policy $\pi_{\theta_i}$ to generate a number of trajectories. We then choose a subset of $N$ states along these trajectories, denoted $s_1, s_2, \dots, s_N$, which we call the "rollout set". For each state $s_n$ in the rollout set, we sample $K$ actions according to $a_{n,k} \sim q(\cdot |  s_n)$. Any choice of $q(\cdot | s_n)$ with a support that includes the support of $\pi_{\theta_i}(\cdot | s_n)$ will produce a consistent estimator. In practice, we found that $q(\cdot | s_n) = \pi_{\theta_i}(\cdot | s_n)$ works well on continuous problems, such as robotic locomotion, while the uniform distribution works well on discrete tasks, such as the Atari games, where it can sometimes achieve better exploration.

For each action $a_{n,k}$ sampled at each state $s_n$, we estimate $\hat{Q}_{\theta_i}(s_n, a_{n,k})$ by performing a rollout (i.e., a short trajectory) starting with state $s_n$ and action $a_{n,k}$. We can greatly reduce the variance of the $Q$-value differences between rollouts by using the same random number sequence for the noise in each of the $K$ rollouts, i.e., *common random numbers*. See [1] for additional discussion on Monte Carlo estimation of $Q$-values and [23] for a discussion of common random numbers in reinforcement learning.

In small, finite action spaces, we can generate a rollout for every possible action from a given state. The contribution to $L_{\theta_{\mathrm{old}}}$ from a single state $s_n$ is as follows:

$$
\begin{align}

L_n(\theta) = \sum_{k=1}^K \pi_{\theta}(a_k | s_n) \hat{Q}(s_n,a_k), \tag{15}
\end{align}
$$

where the action space is $\mathcal{A} = \left\{a_1,a_2,\dots,a_K\right\}$. In large or continuous state spaces, we can construct an estimator of the surrogate objective using importance sampling. The self-normalized estimator ([24], Chapter 9) of $L_{\theta_{\mathrm{old}}}$ obtained at a single state $s_n$ is

$$
\begin{align}

L_n(\theta) =
\frac
{\sum_{k=1}^K \frac{\pi_{\theta}(a_{n,k} | s_n)}{\pi_{\theta_{\mathrm{old}}}(a_{n,k} | s_n)} \hat{Q}(s_n,a_{n,k})}
{\sum_{k=1}^K \frac{\pi_{\theta}(a_{n,k} | s_n)}{\pi_{\theta_{\mathrm{old}}}(a_{n,k} | s_n)} }, \tag{16}
\end{align}
$$

assuming that we performed $K$ actions $a_{n,1}, a_{n,2}, \dots, a_{n,K}$ from state $s_n$. This self-normalized estimator removes the need to use a baseline for the $Q$-values (note that the gradient is unchanged by adding a constant to the $Q$-values). Averaging over $s_n \sim \rho(\pi)$, we obtain an estimator for $L_{\theta_{\mathrm{old}}}$, as well as its gradient.

The *vine* and *single path* methods are illustrated in Figure 1. We use the term *vine*, since the trajectories used for sampling can be likened to the stems of vines, which branch at various points (the rollout set) into several short offshoots (the rollout trajectories).

The benefit of the *vine* method over the *single path* method that is our local estimate of the objective has much lower variance given the same number of $Q$-value samples in the surrogate objective. That is, the *vine* method gives much better estimates of the advantage values. The downside of the *vine* method is that we must perform far more calls to the simulator for each of these advantage estimates. Furthermore, the *vine* method requires us to generate multiple trajectories from each state in the rollout set, which limits this algorithm to settings where the system can be reset to an arbitrary state. In contrast, the single path algorithm requires no state resets and can be directly implemented on a physical system [19].

## 6. Practical Algorithm

Here we present two practical policy optimization algorithm based on the ideas above, which use either the *single path* or *vine* sampling scheme from the preceding section. The algorithms repeatedly perform the following steps:

1.  Use the *single path* or *vine* procedures to collect a set of state-action pairs along with Monte Carlo estimates of their $Q$-values.

2.  By averaging over samples, construct the estimated objective and constraint in Equation (14).

3.  Approximately solve this constrained optimization problem to update the policy's parameter vector $\theta$. We use the conjugate gradient algorithm followed by a line search, which is altogether only slightly more expensive than computing the gradient itself. See Appendix C for details.

With regard to (3), we construct the Fisher information matrix (FIM) by analytically computing the Hessian of the KL divergence, rather than using the covariance matrix of the gradients. That is, we estimate $A_{ij}$ as $\frac{1}{N}\sum_{n=1}^N \frac{\partial^2}{\partial\theta_i \partial \theta_j} D_{\rm KL}(\pi_{\theta_{\mathrm{old}}}(\cdot | s_n) \ \| \ \pi_{\theta}(\cdot | s_n))$, rather than $\frac{1}{N} \sum_{n=1}^N \frac{\partial}{\partial\theta_i}\log \pi_{\theta}(a_n | s_n) \frac{\partial}{\partial\theta_j}\log \pi_{\theta}(a_n | s_n)$. The analytic estimator integrates over the action at each state $s_n$, and does not depend on the action $a_n$ that was sampled. As described in Appendix C, this analytic estimator has computational benefits in the large-scale setting, since it removes the need to store a dense Hessian or all policy gradients from a batch of trajectories. The rate of improvement in the policy is similar to the empirical FIM, as shown in the experiments.

Let us briefly summarize the relationship between the theory from Section 3 and the practical algorithm we have described:

- The theory justifies optimizing a surrogate objective with a penalty on KL divergence. However, the large penalty coefficient $C$ leads to prohibitively small steps, so we would like to decrease this coefficient. Empirically, it is hard to robustly choose the penalty coefficient, so we use a hard constraint instead of a penalty, with parameter $\delta$ (the bound on KL divergence).

- The constraint on ${D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}},\theta)$ is hard for numerical optimization and estimation, so instead we constrain ${\overline D_{\rm KL}^{}}(\theta_{\mathrm{old}},\theta)$.

- Our theory ignores estimation error for the advantage function. [11] consider this error in their derivation, and the same arguments would hold in the setting of this paper, but we omit them for simplicity.

## 7. Connections with Prior Work

As mentioned in Section 4, our derivation results in a policy update that is related to several prior methods, providing a unifying perspective on a number of policy update schemes. The natural policy gradient [25] can be obtained as a special case of the update in Equation (12) by using a linear approximation to $L$ and a quadratic approximation to the ${\overline D_{\rm KL}^{}}$ constraint, resulting in the following problem:

$$
\begin{align}

&\operatorname*{maximize}_{\theta} \left[ \nabla_{\theta} L_{\theta_{\mathrm{old}}}(\theta)\big\rvert_{\theta=\theta_{\mathrm{old}}} \cdot (\theta - \theta_{\mathrm{old}}) \right] \tag{17} \\
&\text{\ \  subject to }  \frac{1}{2} (\theta_{\mathrm{old}} - \theta)^T A(\theta_{\mathrm{old}}) (\theta_{\mathrm{old}} - \theta) \le \delta, \\
& \text{\ \ where } A(\theta_{\mathrm{old}})_{ij} = \\
& \quad \frac{\partial}{\partial\theta_i}\frac{\partial}{\partial\theta_j}   \mathbb{E}_{s \sim \rho_{\pi}}\left[ D_{\rm KL}(\pi(\cdot |  s, \theta_{\mathrm{old}}) \ \| \ \pi(\cdot |  s, \theta)) \right]\big\rvert_{\theta=\theta_{\mathrm{old}}}.
\end{align}
$$

The update is $\theta_{\mathrm{new}} = \theta_{\mathrm{old}} + \frac{1}{\lambda} A(\theta_{\mathrm{old}})^{-1} \nabla_{\theta} L(\theta)\big\rvert_{\theta=\theta_{\mathrm{old}}}$, where the stepsize $\frac{1}{\lambda}$ is typically treated as an algorithm parameter. This differs from our approach, which enforces the constraint at each update. Though this difference might seem subtle, our experiments demonstrate that it significantly improves the algorithm's performance on larger problems.

We can also obtain the standard policy gradient update by using an $\ell_2$ constraint or penalty:

$$
\begin{align}

&\operatorname*{maximize}_{\theta}  \left[\nabla_{\theta} L_{\theta_{\mathrm{old}}}(\theta)\big\rvert_{\theta=\theta_{\mathrm{old}}} \cdot (\theta - \theta_{\mathrm{old}})\right] \tag{18} \\
&\text{\ \  subject to }  \frac{1}{2} \|\theta - \theta_{\mathrm{old}}\|^2 \le \delta.
\end{align}
$$

The policy iteration update can also be obtained by solving the unconstrained problem $\operatorname*{maximize}_{\pi} L_{\pi_{\mathrm{old}}}(\pi)$, using $L$ as defined in Equation (3).

Several other methods employ an update similar to Equation (12). *Relative entropy policy search* (REPS) [20] constrains the state-action marginals $p(s, a)$, while TRPO constrains the conditionals $p(a | s)$. Unlike REPS, our approach does not require a costly nonlinear optimization in the inner loop. Levine and Abbeel also use a KL divergence constraint, but its purpose is to encourage the policy not to stray from regions where the estimated dynamics model is valid, while we do not attempt to estimate the system dynamics explicitly. [27] also build on and generalize Kakade and Langford's results, and they derive different algorithms from the ones here.

## 8. Experiments

We designed our experiments to investigate the following questions:

1.  What are the performance characteristics of the *single path* and *vine* sampling procedures?

2.  TRPO is related to prior methods (e.g. natural policy gradient) but makes several changes, most notably by using a fixed KL divergence rather than a fixed penalty coefficient. How does this affect the performance of the algorithm?

3.  Can TRPO be used to solve challenging large-scale problems? How does TRPO compare with other methods when applied to large-scale problems, with regard to final performance, computation time, and sample complexity?

To answer (1) and (2), we compare the performance of the *single path* and *vine* variants of TRPO, several ablated variants, and a number of prior policy optimization algorithms. With regard to (3), we show that both the *single path* and *vine* algorithm can obtain high-quality locomotion controllers from scratch, which is considered to be a hard problem. We also show that these algorithms produce competitive results when learning policies for playing Atari games from images using convolutional neural networks with tens of thousands of parameters.

<p><img src="assets/mjcmodels2.png" style="width: 100%;" /></p>

Figure: 2D robot models used for locomotion experiments. From left to right: swimmer, hopper, walker. The hopper and walker present a particular challenge, due to underactuation and contact discontinuities.

### 8.1. Simulated Robotic Locomotion

<p><img src="assets/kinematic-network.png" style="height: 3.5cm;" />
<img src="assets/network.png" style="height: 3.5cm;" /></p>

Figure: Neural networks used for the locomotion task (top) and for playing Atari games (bottom).

We conducted the robotic locomotion experiments using the MuJoCo simulator [28]. The three simulated robots are shown in Figure 2. The states of the robots are their generalized positions and velocities, and the controls are joint torques. Underactuation, high dimensionality, and non-smooth dynamics due to contacts make these tasks very challenging. The following models are included in our evaluation:

1.  *Swimmer*. $10$-dimensional state space, linear reward for forward progress and a quadratic penalty on joint effort to produce the reward $r(x,u) = v_x - 10^{-5}\|u\|^2$. The swimmer can propel itself forward by making an undulating motion.

2.  *Hopper*. $12$-dimensional state space, same reward as the swimmer, with a bonus of $+1$ for being in a non-terminal state. We ended the episodes when the hopper fell over, which was defined by thresholds on the torso height and angle.

3.  *Walker*. $18$-dimensional state space. For the walker, we added a penalty for strong impacts of the feet against the ground to encourage a smooth walk rather than a hopping gait.

We used $\delta=0.01$ for all experiments. See Table 2 in the Appendix for more details on the experimental setup and parameters used. We used neural networks to represent the policy, with the architecture shown in Figure 3, and further details provided in Appendix D. To establish a standard baseline, we also included the classic cart-pole balancing problem, based on the formulation from [29], using a linear policy with six parameters that is easy to optimize with derivative-free black-box optimization methods.

The following algorithms were considered in the comparison: *single path TRPO*; *vine TRPO*; *cross-entropy method* (CEM), a gradient-free method [3]; *covariance matrix adaption* (CMA), another gradient-free method [30]; *natural gradient*, the classic natural policy gradient algorithm [25], which differs from *single path* by the use of a fixed penalty coefficient (Lagrange multiplier) instead of the KL divergence constraint; *empirical FIM*, identical to *single path*, except that the FIM is estimated using the covariance matrix of the gradients rather than the analytic estimate; *max KL*, which was only tractable on the cart-pole problem, and uses the maximum KL divergence in Equation (11), rather than the average divergence, allowing us to evaluate the quality of this approximation. The parameters used in the experiments are provided in Appendix E. For the *natural gradient* method, we swept through the possible values of the stepsize in factors of three, and took the best value according to the final performance.

<p><img src="assets/Cartpole.png" style="width: 40%;" />
<img src="assets/Swimmer.png" style="width: 40%;" /><br />
<img src="assets/Hopper.png" style="width: 40%;" />
<img src="assets/Walker.png" style="width: 40%;" /></p>

Figure: Learning curves for locomotion tasks, averaged across five runs of each algorithm with random initializations. Note that for the hopper and walker, a score of $-1$ is achievable without any forward velocity, indicating a policy that simply learned balanced standing, but not walking.

Learning curves showing the total reward averaged across five runs of each algorithm are shown in Figure 4. *Single path* and *vine* TRPO solved all of the problems, yielding the best solutions. *Natural gradient* performed well on the two easier problems, but was unable to generate hopping and walking gaits that made forward progress. These results provide empirical evidence that constraining the KL divergence is a more robust way to choose step sizes and make fast, consistent progress, compared to using a fixed penalty. CEM and CMA are derivative-free algorithms, hence their sample complexity scales unfavorably with the number of parameters, and they performed poorly on the larger problems. The *max KL* method learned somewhat more slowly than our final method, due to the more restrictive form of the constraint, but overall the result suggests that the average KL divergence constraint has a similar effect as the theorecally justified maximum KL divergence. Videos of the policies learned by TRPO may be viewed on the project website: <http://sites.google.com/site/trpopaper/>.

Note that TRPO learned all of the gaits with general-purpose policies and simple reward functions, using minimal prior knowledge. This is in contrast with most prior methods for learning locomotion, which typically rely on hand-architected policy classes that explicitly encode notions of balance and stepping [31, 32, 6].

|  | B. Rider | Breakout | Enduro | Pong | Q*bert | Seaquest | S. Invaders |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Random | 354 | 1.2 | 0 | $-20.4$ | 157 | 110 | 179 |
| Human [33] | 7456 | 31.0 | 368 | $-3.0$ | 18900 | 28010 | 3690 |
| Deep Q Learning [33] | 4092 | 168.0 | 470 | 20.0 | 1952 | 1705 | 581 |
| UCC-I [34] | 5702 | 380 | 741 | 21 | 20025 | 2995 | 692 |
| TRPO - single path | 1425.2 | 10.8 | 534.6 | 20.9 | 1973.5 | 1908.6 | 568.4 |
| TRPO - vine | 859.5 | 34.2 | 430.8 | 20.9 | 7732.5 | 788.4 | 450.2 |

Table: Performance comparison for vision-based RL algorithms on the Atari domain. Our algorithms (bottom rows) were run once on each task, with the same architecture and parameters. Performance varies substantially from run to run (with different random initializations of the policy), but we could not obtain error statistics due to time constraints.

### 8.2. Playing Games from Images

To evaluate TRPO on a partially observed task with complex observations, we trained policies for playing Atari games, using raw images as input. The games require learning a variety of behaviors, such as dodging bullets and hitting balls with paddles. Aside from the high dimensionality, challenging elements of these games include delayed rewards (no immediate penalty is incurred when a life is lost in Breakout or Space Invaders); complex sequences of behavior (Q\*bert requires a character to hop on $21$ different platforms); and non-stationary image statistics (Enduro involves a changing and flickering background).

We tested our algorithms on the same seven games reported on in [33] and [34], which are made available through the Arcade Learning Environment [35] The images were preprocessed following the protocol in Mnih et al , and the policy was represented by the convolutional neural network shown in Figure 3, with two convolutional layers with $16$ channels and stride $2$, followed by one fully-connected layer with $20$ units, yielding 33,500 parameters.

The results of the *vine* and *single path* algorithms are summarized in Table 1, which also includes an expert human performance and two recent methods: deep $Q$-learning [33], and a combination of Monte-Carlo Tree Search with supervised training [34], called UCC-I. The 500 iterations of our algorithm took about 30 hours (with slight variation between games) on a 16-core computer. While our method only outperformed the prior methods on some of the games, it consistently achieved reasonable scores. Unlike the prior methods, our approach was not designed specifically for this task. The ability to apply the same policy search method to methods as diverse as robotic locomotion and image-based game playing demonstrates the generality of TRPO.

## 9. Discussion

We proposed and analyzed trust region methods for optimizing stochastic control policies. We proved monotonic improvement for an algorithm that repeatedly optimizes a local approximation to the expected return of the policy with a KL divergence penalty, and we showed that an approximation to this method that incorporates a KL divergence constraint achieves good empirical results on a range of challenging policy learning tasks, outperforming prior methods. Our analysis also provides a perspective that unifies policy gradient and policy iteration methods, and shows them to be special limiting cases of an algorithm that optimizes a certain objective subject to a trust region constraint.

In the domain of robotic locomotion, we successfully learned controllers for swimming, walking and hopping in a physics simulator, using general purpose neural networks and minimally informative rewards. To our knowledge, no prior work has learned controllers from scratch for all of these tasks, using a generic policy search method and non-engineered, general-purpose policy representations. In the game-playing domain, we learned convolutional neural network policies that used raw images as inputs. This requires optimizing extremely high-dimensional policies, and only two prior methods report successful results on this task.

Since the method we proposed is scalable and has strong theoretical foundations, we hope that it will serve as a jumping-off point for future work on training large, rich function approximators for a range of challenging problems. At the intersection of the two experimental domains we explored, there is the possibility of learning robotic control policies that use vision and raw sensory data as input, providing a unified scheme for training robotic controllers that perform both perception and control. The use of more sophisticated policies, including recurrent policies with hidden state, could further make it possible to roll state estimation and control into the same policy in the partially-observed setting. By combining our method with model learning, it would also be possible to substantially reduce its sample complexity, making it applicable to real-world settings where samples are expensive.

## 10. Acknowledgements

We thank Emo Todorov and Yuval Tassa for providing the MuJoCo simulator; Bruno Scherrer, Tom Erez, Greg Wayne, and the anonymous ICML reviewers for insightful comments, and Vitchyr Pong and Shane Gu for pointing our errors in a previous version of the manuscript. This research was funded in part by the Office of Naval Research through a Young Investigator Award and under grant number N00014-11-1-0688, DARPA through a Young Faculty Award, by the Army Research Office through the MAST program.

# References

[1] Dimitri P. Bertsekas. Dynamic Programming and Optimal Control. 2005.
[2] Jan Peters, Stefan Schaal. Reinforcement Learning of Motor Skills with Policy Gradients. 2008.
[3] István Szita, András Lörincz. Learning Tetris Using the Noisy Cross-Entropy Method. 2006.
[4] [missing author for bertsekas2011approximate]. [missing title for bertsekas2011approximate]. [missing year for bertsekas2011approximate].
[5] Victor Gabillon, Mohammad Ghavamzadeh, Bruno Scherrer. Approximate Dynamic Programming Finally Performs Well in the Game of Tetris. 2013.
[6] Kevin Wampler, Zoran Popović. Optimal Gait and Form for Animal Locomotion. 2009.
[7] Arkadi Nemirovski. Efficient Methods in Convex Programming. 2005.
[8] [missing author for shamir2012complexity]. [missing title for shamir2012complexity]. [missing year for shamir2012complexity].
[9] [missing author for duchi2013optimal]. [missing title for duchi2013optimal]. [missing year for duchi2013optimal].
[10] Marc Peter Deisenroth, Gerhard Neumann, Jan Peters. A Survey on Policy Search for Robotics. 2013.
[11] Sham M. Kakade, John Langford. Approximately Optimal Approximate Reinforcement Learning. 2002.
[12] David Pollard. Asymptopia: An Exposition of Statistical Asymptotic Theory. 2000.
[13] David R. Hunter, Kenneth Lange. A Tutorial on MM Algorithms. 2004.
[14] [missing author for parikh2013proximal]. [missing title for parikh2013proximal]. [missing year for parikh2013proximal].
[15] [missing author for shalev2011online]. [missing title for shalev2011online]. [missing year for shalev2011online].
[16] [missing author for kivinen1997exponentiated]. [missing title for kivinen1997exponentiated]. [missing year for kivinen1997exponentiated].
[17] Jorge Nocedal, Stephen J. Wright. Numerical Optimization. 1999.
[18] J. Andrew Bagnell, Jeff G. Schneider. Covariant Policy Search. 2003.
[19] Jan Peters, Stefan Schaal. Natural Actor-Critic. 2008.
[20] Jan Peters, Katharina Mülling, Yasemin Altün. Relative Entropy Policy Search. 2010.
[21] Peter L. Bartlett, Jonathan Baxter. Infinite-Horizon Policy-Gradient Estimation. 2011.
[22] Michail G. Lagoudakis, Ronald Parr. Reinforcement Learning as Classification: Leveraging Modern Classifiers. 2003.
[23] Andrew Y. Ng, Michael I. Jordan. PEGASUS: A Policy Search Method for Large MDPs and POMDPs. 2000.
[24] Art B. Owen. Monte Carlo Theory, Methods and Examples. 2013.
[25] Sham M. Kakade. A Natural Policy Gradient. 2002.
[26] Sergey Levine, Pieter Abbeel. Learning Neural Network Policies with Guided Policy Search under Unknown Dynamics. 2014.
[27] Matteo Pirotta, Marcello Restelli, Alessio Pecorino, Daniele Calandriello. Safe Policy Iteration. 2013.
[28] Emanuel Todorov, Tom Erez, Yuval Tassa. MuJoCo: A Physics Engine for Model-Based Control. 2012.
[29] Andrew G. Barto, Richard S. Sutton, Charles W. Anderson. Neuronlike Adaptive Elements That Can Solve Difficult Learning Control Problems. 1983.
[30] Nikolaus Hansen, Andreas Ostermeier. Adapting Arbitrary Normal Mutation Distributions in Evolution Strategies: The Covariance Matrix Adaptation. 1996.
[31] Russ Tedrake, Teresa Weirui Zhang, H. Sebastian Seung. Stochastic Policy Gradient Reinforcement Learning on a Simple 3D Biped. 2004.
[32] Tao Geng, Bernd Porr, Florentin Wörgötter. Fast Biped Walking with a Reflexive Controller and Real-Time Policy Searching. 2006.
[33] Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Alex Graves, Ioannis Antonoglou, Daan Wierstra, Martin A. Riedmiller. Playing Atari with Deep Reinforcement Learning. 2013.
[34] Xiaoxiao Guo, Satinder Singh, Honglak Lee, Richard L. Lewis, Xiaoshi Wang. Deep Learning for Real-Time Atari Game Play Using Offline Monte-Carlo Tree Search Planning. 2014.
[35] Marc G. Bellemare, Yavar Naddaf, Joel Veness, Michael Bowling. The Arcade Learning Environment: An Evaluation Platform for General Agents. 2013.
[36] David A. Levin, Yuval Peres, Elizabeth L. Wilmer. Markov Chains and Mixing Times. 2009.
[37] James Martens, Ilya Sutskever. Training Deep and Recurrent Networks with Hessian-Free Optimization. 2012.
[38] Razvan Pascanu, Yoshua Bengio. Revisiting Natural Gradient for Deep Networks. 2013.
[39] [missing author for fu2006gradient]. [missing title for fu2006gradient]. [missing year for fu2006gradient].

# Appendix

## A. Proof of Policy Improvement Bound

This proof (of Theorem 1) uses techniques from the proof of Theorem 4.1 in [11], adapting them to the more general setting considered in this paper. An informal overview is as follows. Our proof relies on the notion of coupling, where we jointly define the policies $\pi$ and $\tilde\pi$ so that <u>they choose the same action with high probability</u> $=(1-\alpha)$. Surrogate loss $L_{\pi}(\tilde{\pi})$ accounts for the the advantage of $\tilde{\pi}$ **the first time** that it disagrees with $\pi$, but **not subsequent disagreements**. Hence, the error in $L_{\pi}$ is due to two or more disagreements between $\pi$ and $\tilde{\pi}$, hence, we get an $O(\alpha^2)$ correction term, where $\alpha$ is the probability of disagreement.

We start out with a lemma from [11] that shows that the difference in policy performance $\eta(\tilde{\pi}) - \eta(\pi)$ can be decomposed as a sum of per-timestep advantages.

**Lemma 1**. Given two policies $\pi,\tilde{\pi}$,

$$
\begin{align}

\eta(\tilde{\pi}) = \eta(\pi) +  &\mathbb{E}_{\tau \sim \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t A_{\pi}(s_t, a_t)\right] \tag{19}
\end{align}
$$

This expectation is taken over trajectories $\tau := (s_0, a_0, s_1, a_0, \dots)$, and the notation $\mathbb{E}_{\tau \sim \tilde{\pi}}\left[\dots\right]$ indicates that actions are sampled from $\tilde{\pi}$ to generate $\tau$.

**Proof.** First note that $A_{\pi}(s,a) = \mathbb{E}_{s' \sim P(s' | s,a)}\left[r(s) + \gamma V_{\pi}(s') - V_{\pi}(s)\right]$. Therefore,

$$
\begin{align}

&\mathbb{E}_{\tau | \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t A_{\pi}(s_t, a_t)\right] \tag{20} \\
&= \mathbb{E}_{\tau | \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t (r(s_t) + \gamma V_{\pi}(s_{t+1}) - V_{\pi}(s_t))\right] \tag{21} \\
&= \mathbb{E}_{\tau | \tilde{\pi}}\left[-V_{\pi}(s_0)+ \sum_{t=0}^{\infty} \gamma^t r(s_t)\right] \tag{22} \\
&= -\mathbb{E}_{s_0}\left[V_{\pi}(s_0)\right]+\mathbb{E}_{\tau | \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t r(s_t)\right] \tag{23} \\
&=  -\eta(\pi) + \eta(\tilde{\pi}) \tag{24}
\end{align}
$$

Rearranging, the result follows. ◻

Define $\bar{A}(s)$ to be the expected advantage of $\tilde{\pi}$ over $\pi$ at state $s$:

$$
\begin{align}

\bar{A}(s) = \mathbb{E}_{a \sim \tilde{\pi}(\cdot | s)}\left[A_{\pi}(s, a)\right]. \tag{25}
\end{align}
$$

Now Lemma 1 can be written as follows:[^3]

$$
\begin{align}

\eta(\tilde{\pi}) = \eta(\pi) + \mathbb{E}_{\tau \sim \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t \bar{A}(s_t)\right] \tag{26}
\end{align}
$$

Note that $L_{\pi}$ can be written as

$$
\begin{align}

L_{\pi}(\tilde{\pi}) = \eta(\pi) + \mathbb{E}_{\tau \sim \pi}\left[\sum_{t=0}^{\infty} \gamma^t \bar{A}(s_t)\right] \tag{27}
\end{align}
$$

The difference in these equations is whether the states are sampled using $\pi$ or $\tilde{\pi}$. To bound the difference between $\eta(\tilde{\pi})$ and $L_{\pi}(\tilde{\pi})$, we will bound the difference arising from each timestep. To do this, we first need to introduce a measure of how much $\pi$ and $\tilde{\pi}$ agree. Specifically, we'll *couple* the policies, so that they define a joint distribution over pairs of actions.

**Definition 1**. $(\pi,\tilde{\pi})$ is an *$\alpha$-coupled policy pair* if it defines a joint distribution $(a,\tilde{a}) | s$, such that $P(a \neq \tilde{a} | s) \le \alpha$ for all $s$. $\pi$ and $\tilde{\pi}$ will denote the marginal distributions of $a$ and $\tilde{a}$, respectively.

Computationally, $\alpha$-coupling means that if we randomly choose a seed for our random number generator, and then we sample from each of $\pi$ and $\tilde{\pi}$ after setting that seed, the results will agree for at least fraction $1 - \alpha$ of seeds.

**Lemma 2**. Given that $\pi, \tilde{\pi}$ are $\alpha$-coupled policies, for all $s$,

$$
\begin{align}

|\bar{A}(s)| \le 2 \alpha \max_{s,a}{|A_{\pi}(s,a)|} \tag{28}
\end{align}
$$

**Proof.**

$$
\begin{align}

\bar{A}(s) &= \mathbb{E}_{\tilde{a} \sim \tilde{\pi}}\left[A_{\pi}(s,\tilde{a})\right] =\mathbb{E}_{(a,\tilde{a}) \sim (\pi,\tilde{\pi})}\left[A_{\pi}(s,\tilde{a}) - A_{\pi}(s, a)\right] \quad\text{since \quad}\mathbb{E}_{a \sim \pi}\left[A_{\pi}(s,a)\right]=0 \tag{29} \\
&= P(a \neq \tilde{a} | s) \mathbb{E}_{(a,\tilde{a}) \sim (\pi,\tilde{\pi}) | a \neq \tilde{a}}\left[A_{\pi}(s,\tilde{a}) - A_{\pi}(s, a)\right] \tag{30} \\
|\bar{A}(s)| &\le \alpha \cdot 2 \max_{s,a}{|A_{\pi}(s,a)|} \tag{31}
\end{align}
$$

Equation (30) uses a conditional-expectation decomposition.[^4]

◻

**Lemma 3**. Let $(\pi,\tilde{\pi})$ be an $\alpha$-coupled policy pair. Then

$$
\begin{align}

|\mathbb{E}_{s_t \sim \tilde{\pi}}\left[\bar{A}(s_t)\right] - \mathbb{E}_{s_t \sim \pi}\left[\bar{A}(s_t)\right]| &\le 2 \alpha \max_s \bar{A}(s)\le 4 \alpha (1 - (1 - \alpha)^t)\max_s |A_{\pi}(s, a)| \tag{32}
\end{align}
$$

**Proof.** Given the coupled policy pair $(\pi, \tilde{\pi})$, we can also obtain a coupling over the trajectory distributions produced by $\pi$ and $\tilde{\pi}$, respectively. Namely, we have pairs of trajectories $\tau, \tilde{\tau}$, where $\tau$ is obtained by taking actions from $\pi$, and $\tilde{\tau}$ is obtained by taking actions from $\tilde{\pi}$, where the same random seed is used to generate both trajectories. We will consider the advantage of $\tilde{\pi}$ over $\pi$ at timestep $t$, and decompose this expectation based on whether $\pi$ agrees with $\tilde{\pi}$ at all timesteps $i<t$.

Let $n_t$ denote the number of times that $a_i \neq \tilde{a}_i$ for $i < t$, i.e., the number of times that $\pi$ and $\tilde{\pi}$ disagree before timestep $t$.

$$
\begin{align}

\mathbb{E}_{s_t \sim \tilde{\pi}}\left[\bar{A}(s_t)\right]
= P(n_t=0)\mathbb{E}_{s_t \sim \tilde{\pi} | n_t = 0}\left[\bar{A}(s_t)\right]
+ P(n_t>0)\mathbb{E}_{s_t \sim \tilde{\pi} | n_t > 0}\left[\bar{A}(s_t)\right] \tag{33}
\end{align}
$$

The expectation decomposes similarly for actions are sampled using $\pi$:

$$
\begin{align}

\mathbb{E}_{s_t \sim \pi}\left[\bar{A}(s_t)\right]
=
P(n_t = 0)
\mathbb{E}_{s_t \sim \pi | n_t = 0}\left[\bar{A}(s_t)\right]
+
P(n_t > 0)
\mathbb{E}_{s_t \sim \pi | n_t > 0}\left[\bar{A}(s_t)\right] \tag{34}
\end{align}
$$

Note that the $n_t=0$ terms are equal:

$$
\begin{align}

\mathbb{E}_{s_t \sim {\color{red} \tilde{\pi}} | n_t = 0}\left[\bar{A}(s_t)\right]=\mathbb{E}_{s_t \sim {\color{red} \pi} | n_t = 0}\left[\bar{A}(s_t)\right], \tag{35}
\end{align}
$$

because $n_t=0$ indicates that $\pi$ and $\tilde{\pi}$ agreed on all timesteps less than $t$. Subtracting Equations (33) and (34), we get

$$
\begin{align}

\mathbb{E}_{s_t \sim \tilde{\pi}}\left[\bar{A}(s_t)\right] - \mathbb{E}_{s_t \sim \pi}\left[\bar{A}(s_t)\right]
&=
P(n_t > 0)
(
\mathbb{E}_{s_t \sim \tilde{\pi} | n_t > 0}\left[\bar{A}(s_t)\right]
- \mathbb{E}_{s_t \sim \pi | n_t > 0}\left[\bar{A}(s_t)\right]
) \tag{36}
\end{align}
$$

By definition of $\alpha$, $P(\pi,\tilde{\pi} \text{ agree at timestep }i) \ge 1-\alpha$, so $P(n_t = 0) \ge (1-\alpha)^t$, and

$$
\begin{align}

P(n_t > 0) \le 1 - (1 - \alpha)^t \tag{37}
\end{align}
$$

Next, note that

$$
\begin{align}

|\mathbb{E}_{s_t \sim \tilde{\pi} | n_t > 0}\left[\bar{A}(s_t)\right] - \mathbb{E}_{s_t \sim \pi | n_t > 0}\left[\bar{A}(s_t)\right]|
&\le |\mathbb{E}_{s_t \sim \tilde{\pi} | n_t > 0}\left[\bar{A}(s_t)\right]| +|\mathbb{E}_{s_t \sim \pi | n_t > 0}\left[\bar{A}(s_t)\right]| \tag{38} \\
&\le 4\alpha \max_{s,a}{|A_{\pi}(s,a)|} \tag{39}
\end{align}
$$

Where the second inequality follows from Lemma 3.

Plugging Equation (37) and Equation (39) into Equation (36), we get

$$
\begin{align}

|\mathbb{E}_{s_t \sim \tilde{\pi}}\left[\bar{A}(s_t)\right]
-
\mathbb{E}_{s_t \sim \pi}\left[\bar{A}(s_t)\right]| \le 4 \alpha (1 - (1 - \alpha)^t) \max_{s,a}{|A_{\pi}(s,a)|} \tag{40}
\end{align}
$$

◻

The preceding Lemma bounds the difference in expected advantage at each timestep $t$. We can sum over time to bound the difference between $\eta(\tilde{\pi})$ and $L_{\pi}(\tilde{\pi})$. Subtracting Equation (26) and Equation (27), and defining $\epsilon=\max_{s,a}{|A_{\pi}(s,a)|}$,

$$
\begin{align}

|\eta(\tilde{\pi}) - L_{\pi}(\tilde{\pi})|
&=\sum_{t=0}^{\infty} \gamma^t |
\mathbb{E}_{\tau \sim \tilde{\pi}}\left[\bar{A}(s_t)\right]-\mathbb{E}_{\tau \sim \pi}\left[\bar{A}(s_t)\right]
| \tag{41} \\
&\le \sum_{t=0}^{\infty} \gamma^t \cdot 4\epsilon \alpha (1 - (1 - \alpha)^t) \tag{42} \\
&= 4\epsilon \alpha \left(\frac{1}{1 - \gamma} - \frac{1}{1 - \gamma(1- \alpha)}\right) \tag{43} \\
&= \frac{4\alpha^2 \gamma \epsilon}{(1 - \gamma)(1 - \gamma(1- \alpha ))} \tag{44} \\
&\le \frac{4\alpha^2 \gamma \epsilon}{(1 - \gamma)^2} \tag{45}
\end{align}
$$

Last, to replace $\alpha$ by the total variation divergence, we need to use the correspondence between TV divergence and coupled random variables:

> Suppose $p_X$ and $p_Y$ are distributions with $D_{TV}(p_X \ \| \ p_Y) = \alpha$. Then there exists a joint distribution $(X,Y)$ whose marginals are $p_X, p_Y$, for which $X = Y$ with probability $1-\alpha$.

See [36], Proposition 4.7.

It follows that if we have two policies $\pi$ and $\tilde{\pi}$ such that $\max_s D_{TV}(\pi(\cdot |  s) \ \| \ \tilde{\pi}(\cdot |  s) ) \le \alpha$, then we can define an $\alpha$-coupled policy pair $(\pi,\tilde{\pi})$ with appropriate marginals. Taking $\alpha=\max_s D_{TV}(\pi(\cdot |  s) \ \| \ \tilde{\pi}(\cdot |  s) ) \le \alpha$ in Equation (45), Theorem 1 follows.

## B. Perturbation Theory Proof of Policy Improvement Bound

We also provide an alternative proof of Theorem 1 using perturbation theory.

**Proof.** Let $G = (1 + \gamma P_{\pi} + (\gamma P_{\pi})^2 + \dots) = (1-\gamma P_{\pi})^{-1}$, and similarly Let $\tilde{G} = (1 + \gamma P_{\tilde{\pi}} + (\gamma P_{\tilde{\pi}})^2 + \dots) = (1-\gamma P_{\tilde{\pi}})^{-1}$. We will use the convention that $\rho$ (a density on state space) is a vector and $r$ (a reward function on state space) is a dual vector (i.e., linear functional on vectors), thus $r \rho$ is a scalar meaning the expected reward under density $\rho$. Note that $\eta(\pi) = rG\rho_0$, and $\eta(\tilde{\pi}) = c \tilde{G} \rho_0$. Let $\Delta = P_{\tilde{\pi}} - P_{\pi}$. We want to bound $\eta(\tilde{\pi}) - \eta(\pi) = r(\tilde{G} - G)\rho_0$. We start with some standard perturbation theory manipulations.

$$
\begin{align}

G^{-1} - \tilde{G}^{-1}
&= (1-\gamma P_{\pi}) - (1-\gamma P_{\tilde{\pi}}) \\
&= \gamma \Delta. \tag{46}
\end{align}
$$

Left multiply by $G$ and right multiply by $\tilde{G}$.

$$
\begin{align}

\tilde{G} - G &= \gamma G \Delta\tilde{G} \\
\tilde{G} &= G + \gamma G \Delta\tilde{G} \tag{47}
\end{align}
$$

Substituting the right-hand side into $\tilde{G}$ gives

$$
\begin{align}

\tilde{G}   &= G + \gamma G \Delta G + \gamma^2 G \Delta G \Delta \tilde{G} \tag{48}
\end{align}
$$

So we have

$$
\begin{align}

\eta(\tilde{\pi}) - \eta(\pi) = r(\tilde{G} - G)\rho = \gamma r G \Delta G \rho_0 + \gamma^2 r G \Delta G \Delta \tilde{G} \rho_0 \tag{49}
\end{align}
$$

Let us first consider the leading term $\gamma r G \Delta G \rho_0$. Note that $rG=v$, i.e., the infinite-horizon state-value function. Also note that $G\rho_0 = \rho_{\pi}$. Thus we can write $\gamma c G \Delta G \rho_0 = \gamma v \Delta \rho_{\pi}$. We will show that this expression equals the expected advantage $L_{\pi}(\tilde{\pi}) - L_{\pi}(\pi)$.

$$
\begin{align}

L_{\pi}(\tilde{\pi}) - L_{\pi}(\pi)
&= \sum_{s} \rho_{\pi}(s) \sum_a (\tilde{\pi}(a |  s) - \pi(a |  s))A_{\pi}(s,a) \\
&= \sum_{s} \rho_{\pi}(s) \sum_a \left(\pi_{\theta}(a| s) - \pi_{\tilde{\theta}}(a |  s)\right) \left[ r(s) + \sum_{s'} p(s'| s,a) \gamma v(s') - v(s)\right] \\
&= \sum_{s} \rho_{\pi}(s)  \sum_{s'} \sum_a \left(\pi(a| s) - \tilde{\pi}(a |  s)\right)  p(s'| s,a) \gamma v(s') \\
&= \sum_{s} \rho_{\pi}(s)  \sum_{s'} (p_{\pi}(s'| s)-p_{\tilde{\pi}}(s'| s)) \gamma v(s') \\
&= \gamma v \Delta \rho_{\pi} \tag{50}
\end{align}
$$

Next let us bound the $O(\Delta^2)$ term $\gamma^2 r G \Delta G \Delta \tilde{G} \rho$. First we consider the product $\gamma r G \Delta = \gamma v \Delta$. Consider the component $s$ of this dual vector.

$$
\begin{align}

|(\gamma v \Delta)_s|
&= |\sum_a (\tilde{\pi}(s,a) - \pi(s,a)) Q_{\pi}(s,a)| \\
&= |\sum_a (\tilde{\pi}(s,a) - \pi(s,a)) A_{\pi}(s,a)| \\
&\le \sum_a |\tilde{\pi}(s,a) - \pi(s,a)| \cdot \max_a |A_{\pi}(s,a)| \\
&\le 2 \alpha \epsilon \tag{51}
\end{align}
$$

where the last line used the definition of the total-variation divergence, and the definition of $\epsilon=\max_{s,a}{|A_{\pi}(s,a)|}$. We bound the other portion $G \Delta \tilde{G} \rho$ using the $\ell_1$ operator norm

$$
\begin{align}

\|A\|_1 = \sup_{\rho} \left\{ \frac{\|A\rho\|_1}{\|\rho\|_1} \right\} \tag{52}
\end{align}
$$

where we have that $\|G\|_1 = \|\tilde{G}\|_1 = 1/(1-\gamma)$ and $\|\Delta\|_1=2\alpha$. That gives

$$
\begin{align}

\|G \Delta \tilde{G} \rho\|_1
&\le \|G\|_1 \|\Delta\|_1 \|\tilde{G}\|_1 \|\rho\|_1 \\
&= \frac{1}{1-\gamma} \cdot 2\alpha \cdot \frac{1}{1-\gamma} \cdot 1 \tag{53}
\end{align}
$$

So we have that

$$
\begin{align}

\gamma^2 |r G \Delta G \Delta \tilde{G} \rho|
&\le \gamma \|\gamma r G \Delta\|_{\infty} \|G \Delta \tilde{G} \rho\|_1 \\
&\le \gamma \|v \Delta\|_{\infty} \|G \Delta \tilde{G} \rho\|_1 \\
&\le \gamma \cdot 2\alpha \epsilon \cdot \frac{2\alpha}{(1-\gamma)^2} \\
&= \frac{4\gamma \epsilon  }{(1-\gamma)^2}\alpha^2 \tag{54}
\end{align}
$$

◻

## C. Efficiently Solving the Trust-Region Constrained Optimization Problem

This section describes how to efficiently approximately solve the following constrained optimization problem, which we must solve at each iteration of TRPO:

$$
\begin{align}

\operatorname*{maximize} L(\theta) \text{\ \  subject to }  {\overline D_{\rm KL}^{}}(\theta_{\mathrm{old}},\theta) \le \delta. \tag{55}
\end{align}
$$

The method we will describe involves two steps: (1) compute a search direction, using a linear approximation to objective and quadratic approximation to the constraint; and (2) perform a line search in that direction, ensuring that we improve the nonlinear objective while satisfying the nonlinear constraint.

The search direction is computed by approximately solving the equation $Ax=g$, where $A$ is the Fisher information matrix, i.e., the quadratic approximation to the KL divergence constraint: ${\overline D_{\rm KL}^{}}(\theta_{\mathrm{old}},\theta) \approx \frac{1}{2} (\theta-\theta_{\mathrm{old}})^T A (\theta-\theta_{\mathrm{old}})$, where $A_{ij} = \frac{\partial}{\partial\theta_i}\frac{\partial}{\partial\theta_j} {\overline D_{\rm KL}^{}}(\theta_{\mathrm{old}},\theta)$. In large-scale problems, it is prohibitively costly (with respect to computation and memory) to form the full matrix $A$ (or $A^{-1}$). However, the conjugate gradient algorithm allows us to approximately solve the equation $Ax=b$ without forming this full matrix, when we merely have access to a function that computes matrix-vector products $y \rightarrow Ay$. Section C.1 describes the most efficient way to compute matrix-vector products with the Fisher information matrix. For additional exposition on the use of Hessian-vector products for optimizing neural network objectives, see [37] and [38].

Having computed the search direction $s \approx A^{-1}g$, we next need to compute the maximal step length $\beta$ such that $\theta + \beta s$ will satisfy the KL divergence constraint. To do this, let $\delta = {\overline D_{\rm KL}^{}} \approx \frac{1}{2} (\beta s)^T A (\beta s) = \frac{1}{2}\beta^2 s^T A s$. From this, we obtain $\beta = \sqrt{2 \delta / s^T A s}$, where $\delta$ is the desired KL divergence. The term $s^T A s$ can be computed through a single Hessian vector product, and it is also an intermediate result produced by the conjugate gradient algorithm.

Last, we use a line search to ensure improvement of the surrogate objective and satisfaction of the KL divergence constraint, both of which are nonlinear in the parameter vector $\theta$ (and thus depart from the linear and quadratic approximations used to compute the step). We perform the line search on the objective $L_{\theta_{\mathrm{old}}}(\theta) - \mathcal{X}[{\overline D_{\rm KL}^{}}(\theta_{\mathrm{old}},\theta) \le \delta]$, where $\mathcal{X}[\dots]$ equals zero when its argument is true and $+\infty$ when it is false. Starting with the maximal value of the step length $\beta$ computed in the previous paragraph, we shrink $\beta$ exponentially until the objective improves. Without this line search, the algorithm occasionally computes large steps that cause a catastrophic degradation of performance.

### C.1. Computing the Fisher-Vector Product

Here we will describe how to compute the matrix-vector product between the averaged Fisher information matrix and arbitrary vectors. This matrix-vector product enables us to perform the conjugate gradient algorithm. Suppose that the parameterized policy maps from the input $x$ to "distribution parameter" vector $\mu_{\theta}(x)$, which parameterizes the distribution $\pi(u | x)$. Now the KL divergence for a given input $x$ can be written as follows:

$$
\begin{align}

D_{\rm KL}(\pi_{\theta_{\mathrm{old}}}(\cdot | x) \ \| \ \pi_{\theta}(\cdot | x)) = \operatorname{kl}(\mu_{\theta}(x),\mu_{\mathrm{old}}) \tag{56}
\end{align}
$$

where $\operatorname{kl}$ is the KL divergence between the distributions corresponding to the two mean parameter vectors. Differentiating $\operatorname{kl}$ twice with respect to $\theta$, we obtain

$$
\begin{align}

\frac{\partial \mu_a(x)}{\partial \theta_i}
\frac{\partial \mu_b(x)}{\partial \theta_j}
\operatorname{kl}''_{ab}(\mu_{\theta}(x),\mu_{\mathrm{old}})
+
\frac{\partial^2 \mu_a(x)}{\partial \theta_i \partial \theta_j} \operatorname{kl}'_{a}(\mu_{\theta}(x),\mu_{\mathrm{old}}) \tag{57}
\end{align}
$$

where the primes ($'$) indicate differentiation with respect to the first argument, and there is an implied summation over indices $a,b$. The second term vanishes, leaving just the first term. Let $J := \frac{\partial \mu_a(x)}{\partial \theta_i}$ (the Jacobian), then the Fisher information matrix can be written in matrix form as $J^T M J$, where $M=kl''_{ab}(\mu_{\theta}(x),\mu_{\mathrm{old}})$ is the Fisher information matrix of the distribution in terms of the mean parameter $\mu$ (as opposed to the parameter $\theta$). This has a simple form for most parameterized distributions of interest.

The Fisher-vector product can now be written as a function $y \rightarrow J^T M J y$. Multiplication by $J^T$ and $J$ can be performed by most automatic differentiation and neural network packages (multiplication by $J^T$ is the well-known backprop operation), and the operation for multiplication by $M$ can be derived for the distribution of interest. Note that this Fisher-vector product is straightforward to average over a set of datapoints, i.e., inputs $x$ to $\mu$.

One could alternatively use a generic method for calculating Hessian-vector products using reverse mode automatic differentiation ([17], chapter 8), computing the Hessian of ${\overline D_{\rm KL}^{}}$ with respect to $\theta$. This method would be slightly less efficient as it does not exploit the fact that the second derivatives of $\mu(x)$ (i.e., the second term in Equation (57)) can be ignored, but may be substantially easier to implement.

We have described a procedure for computing the Fisher-vector product $y \rightarrow Ay$, where the Fisher information matrix is averaged over a set of inputs to the function $\mu$. Computing the Fisher-vector product is typically about as expensive as computing the gradient of an objective that depends on $\mu(x)$ [17]. Furthermore, we need to compute $k$ of these Fisher-vector products per gradient, where $k$ is the number of iterations of the conjugate gradient algorithm we perform. We found $k=10$ to be quite effective, and using higher $k$ did not result in faster policy improvement. Hence, a naïve implementation would spend more than $90\%$ of the computational effort on these Fisher-vector products. However, we can greatly reduce this burden by subsampling the data for the computation of Fisher-vector product. Since the Fisher information matrix merely acts as a metric, it can be computed on a subset of the data without severely degrading the quality of the final step. Hence, we can compute it on $10\%$ of the data, and the total cost of Hessian-vector products will be about the same as computing the gradient. With this optimization, the computation of a natural gradient step $A^{-1} g$ does not incur a significant extra computational cost beyond computing the gradient $g$.

## D. Approximating Factored Policies with Neural Networks

The policy, which is a conditional probability distribution $\pi_{\theta}(a | s)$, can be parameterized with a neural network. This neural network maps (deterministically) from the state vector $s$ to a vector $\mu$, which specifies a distribution over action space. Then we can compute the likelihood $p(a | \mu)$ and sample $a \sim p(a | \mu)$.

For our experiments with continuous state and action spaces, we used a Gaussian distribution, where the covariance matrix was diagonal and independent of the state. A neural network with several fully-connected (dense) layers maps from the input features to the mean of a Gaussian distribution. A separate set of parameters specifies the log standard deviation of each element. More concretely, the parameters include a set of weights and biases for the neural network computing the mean, $\left\{W_i, b_i\right\}_{i=1}^L$, and a vector $r$ (log standard deviation) with the same dimension as $a$. Then, the policy is defined by the normal distribution $\mathcal{N}\left( \operatorname{mean}=\operatorname{NeuralNet}\left(s; \left\{W_i, b_i\right\}_{i=1}^L \right), \operatorname{stdev}=\exp(r) \right)$. Here, $\mu = \left[\operatorname{mean}, \operatorname{stdev}\right]$.

For the experiments with discrete actions (Atari), we use a factored discrete action space, where each factor is parameterized as a categorical distribution. That is, the action consists of a tuple $(a_1, a_2, \dots, a_K)$ of integers $a_k \in \left\{1,2,\dots,N_k\right\}$, and each of these components is assumed to have a categorical distribution, which is specified by a vector $\mu_k = [p_1,p_2, \dots, p_{N_k}]$. Hence, $\mu$ is defined to be the concatenation of the factors' parameters: $\mu = [\mu_1, \mu_2, \dots, \mu_K]$ and has dimension $\dim \mu = \sum_{k=1}^{K} N_k$. The components of $\mu$ are computed by taking applying a neural network to the input $s$ and then applying the softmax operator to each slice, yielding normalized probabilities for each factor.

## E. Experiment Parameters

|  | Swimmer | Hopper | Walker |
| --- | --- | --- | --- |
| State space dim | 10 | 12 | 20 |
| Control space dim | 2 | 3 | 6 |
| Total num. policy params | 364 | 4806 | 8206 |
| Sim. steps per iter | 50K | 1M | 1M |
| Policy iter | 200 | 200 | 200 |
| Stepsize ( ${\overline D_{\rm KL}^{}}{}$ ) | 0.01 | 0.01 | 0.01 |
| Hidden layer size | 30 | 50 | 50 |
| Discount ( $\gamma$ ) | 0.99 | 0.99 | 0.99 |
| Vine: rollout length | 50 | 100 | 100 |
| Vine: rollouts per state | 4 | 4 | 4 |
| Vine: $Q$ -values per batch | 500 | 2500 | 2500 |
| Vine: num. rollouts for sampling | 16 | 16 | 16 |
| Vine: len. rollouts for sampling | 1000 | 1000 | 1000 |
| Vine: computation time (minutes) | 2 | 14 | 40 |
| SP: num. path | 50 | 1000 | 10000 |
| SP: path len | 1000 | 1000 | 1000 |
| SP: computation time | 5 | 35 | 100 |

Table: Parameters for continuous control tasks, vine and single path (SP) algorithms.

|  | All games |
| --- | --- |
| Total num. policy params | 33500 |
| Vine: Sim. steps per iter | 400K |
| SP: Sim. steps per iter | 100K |
| Policy iter | 500 |
| Stepsize ( ${\overline D_{\rm KL}^{}}{}$ ) | 0.01 |
| Discount ( $\gamma$ ) | 0.99 |
| Vine: rollouts per state | $\approx 4$ |
| Vine: computation time | $\approx 30$ hrs |
| SP: computation time | $\approx 30$ hrs |

Table: Parameters used for Atari domain.

## F. Learning Curves for the Atari Domain

<p><img src="assets/beam_rider-crop.png" style="width: 32%;" />
<img src="assets/breakout-crop.png" style="width: 32%;" />
<img src="assets/enduro-crop.png" style="width: 32%;" />
<img src="assets/pong-crop.png" style="width: 32%;" />
<img src="assets/qbert-crop.png" style="width: 32%;" />
<img src="assets/seaquest-crop.png" style="width: 32%;" />
<img src="assets/space_invaders-crop.png" style="width: 32%;" /></p>

Figure: Learning curves for the Atari domain. For historical reasons, the plots show cost = negative reward.

## G. Approximating policies with neural networks

<p><img src="assets/kinematic-network.png" style="width: 60%;" /></p>

Figure: Neural network architecture for the locomotion domain: Two fully connected hidden layers transform the input to the mean $\mu$ of a Normal distribution from which the controls are sampled.

<p><img src="assets/network.png" style="width: 80%;" /></p>

Figure: Neural network architecture for the Atari domain: The screen input is downsampled from $4\times 210\times 160$ to $4\times 52\times 40$, passed through two layers of 16 filters of $4\times 4$ convolutions, flattened and passed through a layer of 20 hidden units. Their output are parameters for a probability distribution from which the actions are sampled.

To represent the stochastic policy $\pi_\theta$, we use a neural network with weights $\theta$. The network maps the observations to a set of parameters indexing the probability distribution that is then used to sample the controls for the rollouts. We now describe the architecture used in the respective domains in more detail.

### G.1. Locomotion domain.

The input $x_0$ of the network are joint angles and velocities as well as cartesian coordinates of body parts. As shown in Figure 3, these are passed through a fully connected layer with a "soft rectifier" nonlinearity $\sigma(x) = \log(1+e^x)$; the final layer uses a softmax nonlinearity to compute the means $\mu = \operatorname{softmax}(W_{12}\cdot \sigma(W_{01} x_0 + b_1) + b_2)$ of a normal distribution; the diagonal covariance matrix $\Sigma$ of this distribution is also learned, but does not depend on $x_0$. Finally, the controls are sampled from $\mathcal N(\mu, \Sigma)$ and clipped to the torque limits.

### G.2. Atari domain.

In the Atari domain, the observations consist of the screen pixels from the last $4$ timesteps; each of these $210\times 160$ images is downsampled by a factor of four. The architecture of the network is shown in Figure 7. We first apply two convolutional layers with $16$ filters each, using tanh nonlinearities and no max pooling. The resulting image is passed through a fully connected layer with 20 units. The final layer uses a softmax nonlinearity to get the probabilities of a multinomial distribution, from which the actions are sampled.

## H. Common Random Numbers

Let us suppose that there are only two actions available $\mathcal{A}=\left\{1,2\right\}$, and we are using the non-importance-sampled estimator eq:algnonsnloss. As above, let $\hat L_{\theta_{\mathrm{old}},n}$ be the contribution to the loss function of a single state $s_n$.

$$
\begin{align}

\nabla_{\theta} \hat{L}_{\theta_{\mathrm{old}},n}(\theta)
&= \nabla_{\theta} \left[ \sum_{a=1,2} \pi_{\theta}(a |  s_n,\theta) \hat Q_{\theta_{\mathrm{old}}}(s_n,a)\right] \\
&= \nabla_{\theta} \left[ \pi_{\theta}(1| s_n,\theta) \hat Q_{\theta_{\mathrm{old}}}(s_n,1) + \pi_{\theta}(2| s_n,\theta) Q_{\theta_{\mathrm{old}}}(s_n,2) \right] \\
&= \nabla_{\theta} \left[ \pi_{\theta}(1| s_n,\theta) \hat Q_{\theta_{\mathrm{old}}}(s_n,1) +(1-\pi_{\theta}(1| s_n,\theta)) \hat Q_{\theta_{\mathrm{old}}}(s_n,2) \right] \\
&= \nabla_{\theta} \pi_{\theta}(1| s_n,\theta) ( \hat Q_{\theta_{\mathrm{old}}}(s_n,1) - \hat Q_{\theta_{\mathrm{old}}}(s_n,2) ) \tag{58}
\end{align}
$$

Thus the variance in our estimate is due to the variance of the $Q$-value difference $\hat Q_{\theta_{\mathrm{old}}}(s_n,1) - \hat Q_{\theta_{\mathrm{old}}}(s_n,2)$.

The method of common random numbers (CRN) allows us to generate a pair of estimates $\hat{Q}_{\theta_{\mathrm{old}}}(s_n,1)$ and $\hat{Q}_{\theta_{\mathrm{old}}}(s_n,2)$ together so that these quantities are correlated and the common noise cancels out when we take the difference. See [24] for an exposition of the technique. There are two sources of randomness for estimating a $Q$-value $\hat Q_{\theta_{\mathrm{old}}}(s,a)$: stochastic policy and stochastic dynamics. Let us suppose that each step of dynamics and each policy decision is a deterministic function of one or more $U(0,1)$ random variables. Let $Z$ be a vector of enough $U(0,1)$ random variables that are needed to do a $T$-step rollout. Then we can write $Q(s,a) = \mathbb{E}_{z \sim Z}\left[Q(s,a,z)\right]$.

Revisiting Equation (58), the variance of each component of $\nabla_{\theta} \hat{L}_n(\theta)$ is proportional to $\mathrm{Var}[( \hat Q_{\theta_{\mathrm{old}}}(s_n,1) - \hat Q_{\theta_{\mathrm{old}}}(s_n,2) )]$. We get the following variances with and without CRN:

$$
\begin{align}

&\mathrm{Var}_{+CRN} = \mathrm{Var}_z[( Q_{\theta_{\mathrm{old}}}(s_n,1,z) - Q_{\theta_{\mathrm{old}}}(s_n,2,z) )] \\
&\mathrm{Var}_{-CRN} = \mathrm{Var}_{z_1, z_2}[( Q_{\theta_{\mathrm{old}}}(s_n,1,z_1) - Q_{\theta_{\mathrm{old}}}(s_n,2,z_2) )] \tag{59}
\end{align}
$$

Letting $\sigma_1^2 = \mathrm{Var}[( Q_{\theta_{\mathrm{old}}}(s_n,1,z)], \sigma_2^2 = \mathrm{Var}[( Q_{\theta_{\mathrm{old}}}(s_n,2,z)]$, and $\rho$ is their correlation coefficient, then the variance with and without CRN is given below. (See [24] for derivation.)

$$
\begin{align}

\mathrm{Var}_{+CRN} &= \sigma_1^2 + \sigma_2^2 - 2 \rho \sigma_1 \sigma_2 \\
\mathrm{Var}_{-CRN} &= \sigma_1^2 + \sigma_2^2 \tag{60}
\end{align}
$$

So $\mathrm{Var}_{+CRN} < \mathrm{Var}_{-CRN}$ whenever the correlation coefficient is positive.

Common random numbers are particularly effective in problems where for a typical pair of actions $a_1, a_2$,

$$
\begin{align}

\frac{|Q(s,a_1)-Q(s,a_2)|}{\sqrt{\mathrm{Var}[\hat{Q}(s,a_1)]}} \ll 1 \tag{61}
\end{align}
$$

where $\mathrm{Var}[\hat{Q}(s,a_1)]$ refers to the variance of a rollout-based estimate of the $Q$-value. The left-hand side of Equation (61) can be interpreted as the signal-to-noise ratio of our $Q$-value estimation procedure. When applying these policy optimization methods to continuous-time control problems, we can choose the time-discretization interval $\Delta t$. Without common random numbers, the signal-to-noise ratio goes to zero in the limit as $\Delta t \rightarrow 0$. However, with common random numbers, the limit is finite.

## I. Lower-variance estimators for importance sampling

For large or infinite action spaces, we use importance sampling (Equation eq:algsnloss), instead of a sum over the action space (Equation eq:algnonsnloss).

Briefly, let us consider the generic problem of estimating $\mathbb{E}_{X\sim p_{\theta}}\left[f(X)\right]$ for some function $f: \mathbb{R}^M \rightarrow \mathbb{R}$ and parameterized probability distribution $p_{\theta}$. The basic importance-sampled estimator for this expectation is

$$
\begin{align}

\hat f_{basic} =
\frac{1}{N} \sum_{n=1}^N \frac{p(x_n)}{q(x_n)} f(x_n), \ \ \ x_n \sim q(x_n) \tag{62}
\end{align}
$$

An alternative estimator is given by the self-normalized importance sampling estimator ([24], Chapter 9), which is biased but typically has lower variance than the estimator in Equation (62)

$$
\begin{align}

\hat f_{sn} =
\frac
{\sum_{n=1}^N \frac{p_{\theta}(x_n)}{q(x_n)} f(x_n)}
{\sum_{n=1}^N \frac{p_{\theta}(x_n)}{q(x_n)} }
, \ \ \ x_n \sim q(x_n). \tag{63}
\end{align}
$$

Now consider the gradient $\nabla_{\theta} \mathbb{E}_{X \sim p_{\theta}}\left[f_{\theta}(X)\right]$.

$$
\begin{align}

\nabla_{\theta} \hat{f}_{sn}
&= \nabla_{\theta} \left[
\frac
{\sum_{n=1}^N \frac{p_{\theta}(x_n)}{q(x_n)} f(x_n)}
{\sum_{n=1}^N \frac{p_{\theta}(x_n)}{q(x_n)} }
\right]
, \ \ \ x_n \sim q(x_n). \tag{64} \\
&= \frac
{\sum_{n=1}^N \frac{\nabla_{\theta} p_{\theta}(x_n)}{q(x_n)} (f(x_n) - \hat{f}_{sn}) }
{\sum_{n=1}^N \frac{p_{\theta}(x_n)}{q(x_n)} }
, \ \ \ x_n \sim q(x_n). \tag{65}
\end{align}
$$

where $\hat{f}_{sn}$ is defined in Equation (63).

There is a large literature on estimating gradients of expectations $\nabla_{\theta} \mathbb{E}_{X \sim p_{\theta}}\left[ f(X) \right]$ (e.g., see [39]). The likelihood ratio estimator is based on the identity $\nabla_{\theta} \mathbb{E}_{X \sim p_{\theta}}\left[ f(X) \right] =  \mathbb{E}_{X \sim p_{\theta}}\left[ \nabla_{\theta} \log p_{\theta}(X) f(X) \right]=\mathbb{E}_{X \sim p_{\theta}}\left[ \nabla_{\theta} \log p_{\theta}(X) (f(X) - \beta)\right]$ where $\beta$ is an arbitrary constant. It is well-known that the variance of this estimator is greatly reduced by using a baseline $\beta \approx \mathbb{E}_{X \sim p_{\theta}}\left[f(X)\right]$. We can see from Equation (63) that by differentiating the self-normalized estimator, we naturally are using a baseline estimate $\hat f_{sn}$, which is formed from our set of samples $x_1, x_2, \dots, x_n$.

Returning to the setting where we are estimating $\hat{L}$, we identify $f$ with the single-sample loss function $L_{\theta_{\mathrm{old}},n}$ and $p_{\theta}$ with the policy $\pi(\cdot |  s_n, \theta)$. Then the estimator for $\hat L_{\theta_{\mathrm{old}},n}$ based on the self-normalized estimator is written

$$
\begin{align}

\hat L_{\theta_{\mathrm{old}}, n}(\theta) =
\frac{
\sum_{k=1}^K \frac{\pi_{\theta}(a_{n,k} |  s_n)}{q(a_{n,k} |  s_n)} \hat Q_{\pi_{\mathrm{old}}}(s_n,a_{n,k})
}
{
\sum_{k=1}^K \frac{\pi_{\theta}(a_{n,k} |  s_n)}{q(a_{n,k} |  s_n)}
}
,\ \ \ a_{n,k} \sim q(\cdot |  s_n). \tag{66}
\end{align}
$$

Typically, a good choice is $q(a |  s_n) = \pi_{\theta_{\mathrm{old}}}(a |  s_n)$, but in some cases it might make sense to use a more uniform distribution.

[^1]: The first-order match comes from comparing Equation (2) and Equation (3). Their difference is

    $\eta(\tilde{\pi}) - L_{\pi}(\tilde{\pi}) = \sum_s (\rho_{\tilde{\pi}}(s) - \rho_{\pi}(s)) \sum_a \tilde{\pi}(a \mid s) A_{\pi}(s,a)$.

    Fix a reference parameter $\theta_0$, write $\pi = \pi_{\theta_0}$, and define
    $g_{\theta}(s) := \sum_a \pi_{\theta}(a \mid s) A_{\pi_{\theta_0}}(s,a)$.
    
    Then
    $\eta(\pi_{\theta}) - L_{\pi_{\theta_0}}(\pi_{\theta}) = \sum_s (\rho_{\pi_{\theta}}(s) - \rho_{\pi_{\theta_0}}(s)) g_{\theta}(s)$.

    The argument now uses the first-order Taylor expansion around $\theta_0$.
    For a scalar-valued differentiable function $f(\theta)$, the expansion is
    $f(\theta) = f(\theta_0) + \nabla_{\theta} f(\theta_0)^{\top}(\theta - \theta_0) + O(\lVert \theta - \theta_0 \rVert^2)$.
    For a vector-valued differentiable function $h(\theta)$, the corresponding formula is
    $h(\theta) = h(\theta_0) + J_h(\theta_0)(\theta - \theta_0) + O(\lVert \theta - \theta_0 \rVert^2)$,
    where $J_h(\theta_0)$ is the Jacobian matrix of $h$ at $\theta_0$.

    The key observation is that $g_{\theta_0}(s) = \sum_a \pi_{\theta_0}(a \mid s) A_{\pi_{\theta_0}}(s,a) = 0$ for every state $s$, because the advantage has zero expectation under the policy that defines it.
    Since $A_{\pi_{\theta_0}}$ is fixed here and each probability $\pi_{\theta}(a \mid s)$ is differentiable in $\theta$, the function $g_{\theta}(s)$ is differentiable as well.
    
    Therefore it has the first-order expansion
    $g_{\theta}(s) = \nabla_{\theta} g_{\theta_0}(s)^{\top}(\theta - \theta_0) + O(\lVert \theta - \theta_0 \rVert^2)$.
    
    In particular, $g_{\theta}(s) = O(\lVert \theta - \theta_0 \rVert)$ near $\theta_0$.

    The visitation frequencies also admit a first-order expansion under the same smoothness assumptions.
    In the finite-state case, the policy induces a transition matrix
    $P_{\pi_{\theta}}(s,s') = \sum_a \pi_{\theta}(a \mid s) P(s' \mid s,a)$,
    which is differentiable in $\theta$ because it is a weighted sum of differentiable policy probabilities.
    The discounted visitation frequency can be written as
    $\rho_{\pi_{\theta}}^{\top} = \rho_0^{\top}(I - \gamma P_{\pi_{\theta}})^{-1}$.
    Since $\gamma < 1$, the inverse exists, and matrix inversion is smooth on the set of invertible matrices.
    Hence $\rho_{\pi_{\theta}}$ is differentiable in $\theta$, giving
    $\rho_{\pi_{\theta}} - \rho_{\pi_{\theta_0}} = J_{\rho}(\theta_0)(\theta - \theta_0) + O(\lVert \theta - \theta_0 \rVert^2)$.
    Thus this factor is also $O(\lVert \theta - \theta_0 \rVert)$.

    Each factor in the product therefore contributes one power of $\lVert \theta - \theta_0 \rVert$, so
    $\eta(\pi_{\theta}) - L_{\pi_{\theta_0}}(\pi_{\theta}) = O(\lVert \theta - \theta_0 \rVert^2)$.
    This shows that the two objectives agree in value and have the same gradient at $\theta_0$, which is exactly what "matches to first order" means.

[^2]: Our result is straightforward to extend to continuous states and actions by replacing the sums with integrals.

[^3]: Equation (26) follows from Lemma 1 by the law of iterated expectation. 
	For each timestep $t$,
	
    $\mathbb{E}_{\tau \sim \tilde{\pi}}\left[A_{\pi}(s_t, a_t)\right]
    = \mathbb{E}_{s_t \sim \tilde{\pi}}\left[
    \mathbb{E}_{a_t \sim \tilde{\pi}(\cdot \mid s_t)}\left[A_{\pi}(s_t, a_t) \mid s_t\right]\right]$.

    By the definition of $\bar{A}(s)$ in Equation (25),

    $\bar{A}(s)
    = \mathbb{E}_{a \sim \tilde{\pi}(\cdot \mid s)}\left[A_{\pi}(s,a)\right]$,

    so

    $\mathbb{E}_{\tau \sim \tilde{\pi}}\left[A_{\pi}(s_t, a_t)\right]
    = \mathbb{E}_{s_t \sim \tilde{\pi}}\left[\bar{A}(s_t)\right]$.

    Substituting this identity into Lemma 1 yields Equation (26):

    $\eta(\tilde{\pi}) = \eta(\pi) + \mathbb{E}_{\tau \sim \tilde{\pi}}\left[\sum_{t=0}^{\infty} \gamma^t \bar{A}(s_t)\right]$.

    For any realized trajectory, each state $s_t$ is paired with one sampled action $a_t$. Under the trajectory distribution, however, after conditioning on $s_t$, the action remains a random variable with conditional law $a_t \sim \tilde{\pi}(\cdot \mid s_t)$. Averaging over that conditional distribution is exactly what produces $\bar{A}(s_t)$.

[^4]: The intuition for Equation (30) is that the difference $A_{\pi}(s,\tilde{a}) - A_{\pi}(s,a)$ contributes only on samples where the two coupled actions disagree. When $a=\tilde{a}$, the difference is zero. Hence the overall average equals the probability of disagreement multiplied by the average difference conditional on disagreement.
