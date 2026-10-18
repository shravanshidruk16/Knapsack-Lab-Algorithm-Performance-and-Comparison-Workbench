"""
Knapsack Lab Configuration
Defines application constants, execution limits, and runner paths.
"""

from pathlib import Path
import platform

BASE_DIR = Path(__file__).resolve().parent

# Executable name depending on platform
RUNNER_FILENAME = "knapsack_runner.exe" if platform.system() == "Windows" else "knapsack_runner"
RUNNER_PATH = BASE_DIR / "algorithms" / RUNNER_FILENAME

# Validation limits
MIN_CAPACITY = 1
MAX_CAPACITY = 2_000_000          # Maximum knapsack capacity for solver
MAX_ITEMS = 500                   # Maximum item count for interactive solver
MAX_ITEM_WEIGHT = 2_000_000       # Maximum single item weight
MAX_ITEM_VALUE = 100_000_000      # Maximum single item value
MAX_DP_CELLS = 30_000_000         # Maximum (N + 1) * (W + 1) table entries

# Benchmark safety limits
MIN_BENCHMARK_ITEMS = 4
MAX_BENCHMARK_ITEMS = 35          # B&B worst-case tree has 2^N states
MAX_BENCHMARK_CASES = 25          # Maximum sample points per benchmark run
MAX_BENCHMARK_REPETITIONS = 10    # Maximum repetitions per point
DEFAULT_EXECUTION_TIMEOUT = 12    # Seconds per algorithm execution

# Flask app configuration
SECRET_KEY = "knapsack-lab-secret-key-cs-mini-project"
DEBUG = False
HOST = "127.0.0.1"
PORT = 5000
