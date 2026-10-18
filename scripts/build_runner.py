#!/usr/bin/env python3
"""
Knapsack Lab — C++ Runner Build Script
Detects available C++17 compiler (g++, clang++, or cl) and compiles the algorithms engine.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ALGORITHMS_DIR = BASE_DIR / "algorithms"

def get_executable_name():
    if platform.system() == "Windows":
        return "knapsack_runner.exe"
    return "knapsack_runner"

def find_compiler():
    # Priority: g++, clang++, cl
    for compiler in ["g++", "clang++", "c++"]:
        path = shutil.which(compiler)
        if path:
            return compiler, path
    
    # Check MSVC cl
    if shutil.which("cl"):
        return "cl", shutil.which("cl")
    
    return None, None

def build():
    compiler, compiler_path = find_compiler()
    if not compiler:
        print("[ERROR] No compatible C++ compiler found (g++, clang++, or cl).", file=sys.stderr)
        print("Please install MinGW-w64, GCC, Clang, or Visual Studio Build Tools.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Using C++ compiler: {compiler} ({compiler_path})")

    exe_name = get_executable_name()
    output_path = ALGORITHMS_DIR / exe_name

    source_files = [
        str(ALGORITHMS_DIR / "knapsack_runner.cpp"),
        str(ALGORITHMS_DIR / "knapsack_dp.cpp"),
        str(ALGORITHMS_DIR / "knapsack_branch_bound.cpp")
    ]

    for src in source_files:
        if not os.path.exists(src):
            print(f"[ERROR] Source file missing: {src}", file=sys.stderr)
            sys.exit(1)

    cmd = []
    if compiler in ["g++", "clang++", "c++"]:
        cmd = [
            compiler,
            "-std=c++17",
            "-O3",
            "-Wall",
            "-Wextra",
            *source_files,
            "-o", str(output_path)
        ]
        if platform.system() == "Windows":
            cmd.append("-lpsapi")
    elif compiler == "cl":
        cmd = [
            "cl",
            "/std:c++17",
            "/O2",
            "/EHsc",
            *source_files,
            f"/Fe:{output_path}",
            "psapi.lib"
        ]

    print(f"[INFO] Executing compilation command:\n  {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ALGORITHMS_DIR), capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Compilation failed with exit code {result.returncode}:", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(f"[SUCCESS] Successfully compiled: {output_path}")

    # Health check
    test_res = subprocess.run([str(output_path), "--health"], capture_output=True, text=True)
    if test_res.returncode == 0:
        print(f"[INFO] Health check passed: {test_res.stdout.strip()}")
    else:
        print(f"[WARN] Health check returned non-zero code {test_res.returncode}: {test_res.stderr.strip()}")

    return str(output_path)

if __name__ == "__main__":
    build()
