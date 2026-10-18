# Benchmark Methodology and Performance Measurement

## 1. Timing Measurement Methodology

### 1.1 Monotonic Timer Design
Measuring algorithm execution accurately requires isolating algorithm logic from I/O, dataset parsing, formatting, and IPC overhead.
- **Windows Implementation:** Uses the Win32 high-resolution counter `QueryPerformanceCounter` and `QueryPerformanceFrequency`. On modern multi-core processors, this hardware counter operates at approximately $10 \text{ MHz}$, yielding a timing resolution of approximately $0.1 \text{ microseconds}$ ($100 \text{ nanoseconds}$).
- **POSIX Implementation:** Uses `std::chrono::steady_clock` with `std::chrono::nanoseconds` resolution.

### 1.2 Isolation of the Timed Region
The timed block in C++ encompasses solely:
- For Dynamic Programming: Table allocation, recurrence nested loops, and backtracking reconstruction.
- For Branch and Bound: Greedy initial feasible solution, priority queue best-first expansions, bound calculations, and index mapping.

Explicitly **excluded** from the measured execution time:
- JSON deserialization and validation.
- Subprocess creation and argument parsing.
- Network and HTTP serialization in Flask.
- Canvas rendering in the client browser.

### 1.3 Statistical Stability via Median of Trials
Because operating systems preempt user-space threads for kernel interrupts and scheduling, a single measurement may register transient spikes.
- The workbench supports configurable repetition trials (default: $3$ to $5$ runs).
- Execution times across trials are sorted, and the **median** runtime is recorded.

---

## 2. Memory Consumption Measurement

### 2.1 Subprocess Process Isolation
To prevent the memory allocations of one algorithm from contaminating the measurements of the other:
- Each algorithm run executes in its own distinct OS subprocess (`knapsack_runner.exe --mode dp` vs `knapsack_runner.exe --mode bb`).
- The Python backend launches independent processes and records their metrics separately.

### 2.2 Operating System Metric: Peak Working Set
- On **Windows**: Measured via `GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))` using `pmc.PeakWorkingSetSize` in bytes.
- On **Linux**: Measured via `getrusage(RUSAGE_SELF, &usage)` where `usage.ru_maxrss` is multiplied by $1,024$ bytes.
- On **macOS**: Measured via `getrusage(RUSAGE_SELF, &usage)` where `usage.ru_maxrss` is reported in bytes.

*Note on Process Memory:* Peak working set reflects the total resident memory paged into RAM by the OS for the short-lived runner process, including C runtime libraries and dynamic linkers.

### 2.3 Explicit Algorithm Workspace Footprint
Alongside OS working set, Knapsack Lab computes the exact heap/stack allocation owned strictly by the algorithm:
- **Dynamic Programming Workspace:**
  $$\text{Bytes}_{\text{DP}} = (N + 1)(W + 1) \times \text{sizeof}(\text{long long}) = (N + 1)(W + 1) \times 8 \text{ bytes}$$
- **Branch and Bound Workspace:**
  $$\text{Bytes}_{\text{BB}} = (\text{Max Frontier Size}) \times \text{sizeof}(\text{BBNode}) + N \times \text{sizeof}(\text{Item})$$

---

## 3. Reproducibility & Seed Handling

### 3.1 Deterministic Pseudo-Random Generation
- Random datasets are generated using Python's `random.Random(seed)`.
- Given a fixed seed, identical weights and values are generated across different machines.
- For parameter sweeps across problem sizes $N$, each benchmark case uses the deterministic progression:
  $$\text{Seed}_N = \text{BaseSeed} + (N \times 1337)$$
This ensures each point is mathematically reproducible while remaining uncorrelated with adjacent sizes.

---

## 4. Safety Constraints & Timeout Guards

### 4.1 Branch and Bound Worst-Case Protection
Because Branch and Bound has exponential worst-case time complexity, difficult instances could stall the server.
- The backend enforces a hard execution timeout (default: $12 \text{ seconds}$) on runner subprocesses using `subprocess.run(..., timeout=timeout)`.
- If an instance exceeds the timeout, the child process is terminated immediately via `proc.kill()`, marked as `timed_out: true`, and earlier benchmark points are preserved.

### 4.2 Dynamic Programming Allocation Protection
To protect against out-of-memory crashes:
- The maximum DP table entries are capped at $30,000,000$ cells (approx. $240 \text{ MB}$).
- If an input violates this bound, the request is rejected with a descriptive validation error before C++ allocation occurs.
