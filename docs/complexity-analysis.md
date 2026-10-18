# Computational Complexity Analysis

## 1. Dynamic Programming Complexity Derivation

### 1.1 Time Complexity: $\mathcal{O}(nW)$
- The algorithm computes a 2D recurrence table consisting of $(n + 1)$ rows and $(W + 1)$ columns.
- For each cell $(i, w)$, the state transition performs a constant number of operations:
  - One comparison: $w_i > w$
  - One subtraction and lookup: $DP[i-1, w - w_i] + v_i$
  - One maximum evaluation: $\max(DP[i-1, w], \dots)$
- Total cell computations:
  $$T(n, W) = \sum_{i=1}^n \sum_{w=0}^W \mathcal{O}(1) = (n + 1)(W + 1) \cdot \mathcal{O}(1) = \mathcal{O}(nW)$$
- Backtracking traverses from row $n$ to row $0$, performing at most $n$ iterations:
  $$T_{\text{backtrack}}(n) = \mathcal{O}(n)$$
- Total execution time is dominated by table construction: $\mathcal{O}(nW)$.

### 1.2 Pseudo-Polynomial Time vs. Strongly Polynomial Time
In computational complexity theory, an algorithm runs in **polynomial time** if its running time is bounded by a polynomial in the *length of the input* (the number of bits required to represent the instance).
- An instance with capacity $W$ requires $L = \lceil \log_2(W + 1) \rceil$ bits to encode.
- Thus, the running time is:
  $$\mathcal{O}(n \cdot W) = \mathcal{O}(n \cdot 2^L)$$
- Because the running time is exponential in the bit length of $W$, 0/1 Knapsack is **NP-hard** in general, and the Dynamic Programming algorithm is **pseudo-polynomial**. When $W$ is polynomially bounded in $n$, the algorithm behaves polynomially.

### 1.3 Space Complexity: $\mathcal{O}(nW)$
- Full solution reconstruction requires storing the entire 2D table of size $(n + 1) \times (W + 1)$ integers (each 8 bytes for 64-bit values).
- Exact memory consumed:
  $$\text{Memory}_{\text{DP}} = (n + 1)(W + 1) \times 8 \text{ bytes}$$
- For example, with $n = 100$ and $W = 100,000$, table memory is:
  $$101 \times 100,001 \times 8 \approx 80.8 \text{ MB}$$

---

## 2. Branch and Bound Complexity Derivation

### 2.1 Worst-Case Time Complexity: $\mathcal{O}(2^n)$
- The state-space decision tree is a complete binary tree of height $n$.
- Total nodes in the full tree:
  $$\sum_{k=0}^n 2^k = 2^{n+1} - 1 = \mathcal{O}(2^n)$$
- At each node, computing the fractional knapsack relaxation upper bound takes at most $\mathcal{O}(n)$ time.
- If no nodes can be pruned (e.g., when all items have identical value-to-weight ratios and fit closely into capacity), all $2^n$ nodes must be expanded:
  $$T_{\text{worst}}(n) = \mathcal{O}(n \cdot 2^n)$$

### 2.2 Best-Case Time Complexity: $\mathcal{O}(n \log n)$
- Initial sorting of $n$ items by ratio takes $\mathcal{O}(n \log n)$.
- The greedy feasible selection takes $\mathcal{O}(n)$.
- If the upper bound at the root node equals the greedy feasible solution value, the root bound immediately matches $V^*_{\text{best}}$.
- The algorithm expands only 1 node, prunes all branches immediately, and terminates:
  $$T_{\text{best}}(n) = \mathcal{O}(n \log n)$$

### 2.3 Space Complexity: $\mathcal{O}(\text{Max Frontier Size})$
- The memory consumed by Branch and Bound is governed by the maximum number of live partial decision states stored in the priority queue (frontier).
- In the worst case, the frontier can contain $\mathcal{O}(2^n)$ nodes.
- In empirical benchmarks with distinct item ratios, the active frontier rarely exceeds a few dozen nodes, consuming under $10$ KB.

---

## 3. Structural Comparison of Crossover Points

| Parameter Variation | Dynamic Programming Behavior | Branch and Bound Behavior | Winner |
| :--- | :--- | :--- | :--- |
| **Capacity $W$ increases from $10^2$ to $10^5$** | Runtime increases linearly by $1,000\times$; memory reaches megabytes | Runtime remains virtually flat (microseconds); bound calculation unaffected | **Branch and Bound** |
| **Problem size $N$ increases to $50+$ with small $W$** | Modest linear runtime increase $\mathcal{O}(nW)$; guaranteed completion | Potential tree explosion if bounds are loose | **Dynamic Programming** |
| **Identical item ratios $\frac{v_i}{w_i} = c$** | Standard $\mathcal{O}(nW)$ performance unaffected | Bound heuristic cannot differentiate subtrees; pruning degrades | **Dynamic Programming** |
| **Highly variable item ratios** | Standard $\mathcal{O}(nW)$ performance unaffected | Bound heuristic is sharp; rapid pruning after 5–20 node expansions | **Branch and Bound** |
