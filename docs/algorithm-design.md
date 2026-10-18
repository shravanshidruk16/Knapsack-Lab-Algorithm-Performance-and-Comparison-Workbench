# Algorithm Design Specification: 0/1 Knapsack

## 1. Problem Formulation

The **0/1 Knapsack Problem** is defined as follows:
Given $n$ items, each characterized by a positive integer weight $w_i \in \mathbb{Z}^+$ and a positive integer value $v_i \in \mathbb{Z}^+$, and a knapsack with positive integer capacity $W \in \mathbb{Z}^+$, select a binary decision vector $x = (x_1, x_2, \dots, x_n) \in \{0, 1\}^n$ such that:

$$\text{Maximize } Z = \sum_{i=1}^n v_i x_i$$

$$\text{Subject to } \sum_{i=1}^n w_i x_i \le W$$

Each item $i$ can either be included entirely ($x_i = 1$) or excluded ($x_i = 0$).

---

## 2. Algorithm 1: Dynamic Programming

### 2.1 Theoretical Foundation & Optimal Substructure
The problem exhibits optimal substructure. Let $DP[i, w]$ represent the maximum value achievable using a subset of the first $i$ items with capacity $w$.

### 2.2 Recurrence Relation
$$DP[0, w] = 0 \quad \forall w \in [0, W]$$

For $i \in [1, n]$ and $w \in [0, W]$:
$$DP[i, w] = \begin{cases}
DP[i-1, w] & \text{if } w_i > w \\
\max\Big(DP[i-1, w],\; DP[i-1, w - w_i] + v_i\Big) & \text{if } w_i \le w
\end{cases}$$

### 2.3 Contiguous Memory Representation
To optimize cache locality and eliminate allocation overhead, the implementation allocates a flat contiguous 1D vector in C++17:
```cpp
std::vector<long long> dp((n + 1) * (capacity + 1), 0LL);
```
Where cell $(i, w)$ is accessed via index $i \times (W + 1) + w$.

### 2.4 Solution Reconstruction (Backtracking)
Beginning at state $(n, W)$:
1. Compare $DP[i, w]$ with $DP[i-1, w]$.
2. If $DP[i, w] \neq DP[i-1, w]$, item $i-1$ was selected. We append its original index, update $w \leftarrow w - w_{i-1}$, and decrement $i \leftarrow i - 1$.
3. If equal, item $i-1$ was omitted; decrement $i \leftarrow i - 1$.
4. Reverse the selected list to present items in their original input order.

---

## 3. Algorithm 2: Branch and Bound

### 3.1 State-Space Decision Tree
Branch and Bound models the solution space as a binary decision tree of depth $n$. At level $k \in [0, n-1]$, the search evaluates decisions for item $k$:
- **Left branch:** Include item $k$ ($x_k = 1$), provided $W_{\text{curr}} + w_k \le W$.
- **Right branch:** Exclude item $k$ ($x_k = 0$).

### 3.2 Sorting by Value-to-Weight Efficiency
Items are sorted in non-increasing order of their efficiency ratio:
$$\frac{v_1}{w_1} \ge \frac{v_2}{w_2} \ge \dots \ge \frac{v_n}{w_n}$$
Deterministic tie-breaking prioritizes higher absolute value, followed by lower weight, and original input index. The mapping to original input indices is strictly preserved.

### 3.3 Fractional Knapsack Relaxation Upper Bound
At any tree node at level $k$ with current weight $W_{\text{curr}}$ and current value $V_{\text{curr}}$, an admissible optimistic upper bound is computed via continuous fractional knapsack relaxation:
1. Greedily incorporate whole items $j \in [k, n-1]$ as long as $W_{\text{curr}} + w_j \le W$.
2. For the first item $m$ that exceeds remaining capacity, include a continuous fraction:
   $$\text{Bound} = V_{\text{curr}} + \sum_{j=k}^{m-1} v_j + (W - W_{\text{tot}}) \times \frac{v_m}{w_m}$$
Because fractional knapsack relaxation is a relaxation of the binary 0/1 constraint, $\text{Bound}(u) \ge Z^*(u)$ for all sub-nodes.

### 3.4 Best-First Search & Pruning Strategy
- Nodes are stored in a max-heap priority queue (`std::priority_queue<BBNode>`) ordered primarily by their upper bound.
- The algorithm seeds the best known feasible objective value $V^*_{\text{best}}$ using a rapid greedy initial feasible selection.
- When node $u$ is extracted from the queue:
  - If $\text{Bound}(u) \le V^*_{\text{best}}$, then because the queue is a max-heap on bound, *no node remaining in the frontier can ever exceed $V^*_{\text{best}}$*. The algorithm increments pruned nodes by $(1 + |PQ|)$ and terminates immediately.
  - Branches are pruned prior to queue insertion if their calculated upper bound is $\le V^*_{\text{best}}$.

---

## 4. Complexity & Performance Profile

| Metric | Dynamic Programming | Branch and Bound |
| :--- | :--- | :--- |
| **Time Complexity** | $\mathcal{O}(nW)$ (Pseudo-polynomial) | $\mathcal{O}(2^n)$ worst-case; $\mathcal{O}(n \log n)$ best-case |
| **Space Complexity** | $\mathcal{O}(nW)$ (2D table for reconstruction) | $\mathcal{O}(2^n)$ worst-case; $\mathcal{O}(\text{Max Frontier})$ |
| **Key Advantage** | Predictable execution on small/moderate $W$ | Dramatic speedup on large $W$ with distinct ratios |
| **Failure Mode** | Memory exhaustion on massive $W$ | Exponential tree explosion on correlated ratios |
