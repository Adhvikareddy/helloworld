"""
Unit tests for strict regulatory and architectural compliance (T5).

Tests:
14a. Grep-equivalent test that fails if any of
     sklearn|scikit|tensorflow|torch|keras|xgboost|lightgbm|catboost|train_test|\\.fit\\(
     appears in any .py file (strict zero-AI/ML policy).
14b. Test that fails if any AI/ML dependencies appear in requirements.txt.
15. Test that fails if git ls-files lists any file matching *_sk.bin or *.pem
    (secret key leakage prevention).
"""
import os
import re
import subprocess
import pytest

FORBIDDEN_PATTERN = re.compile(
    r"sklearn|scikit|tensorflow|torch|keras|xgboost|lightgbm|catboost|train_test|\.fit\("
)


def test_zero_aiml_python_source_compliance():
    """Verify that no AI/ML dependencies or calls exist in Python source files."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    violations = []
    ignore_dirs = {".git", "__pycache__", ".pytest_cache", "venv", ".venv"}
    
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                if os.path.abspath(file_path) == os.path.abspath(__file__):
                    continue
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                    for line_num, line in enumerate(fp, 1):
                        if FORBIDDEN_PATTERN.search(line):
                            violations.append(f"{file_path}:{line_num}: {line.strip()}")
                            
    assert len(violations) == 0, (
        f"AI/ML compliance violation in Python code!\n" + "\n".join(violations)
    )


def test_zero_aiml_requirements_compliance():
    """Verify that requirements.txt has no AI/ML packages."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    req_path = os.path.join(repo_root, "requirements.txt")
    if not os.path.exists(req_path):
        pytest.skip("requirements.txt not found")
        
    violations = []
    with open(req_path, "r", encoding="utf-8") as fp:
        for line_num, line in enumerate(fp, 1):
            if FORBIDDEN_PATTERN.search(line):
                violations.append(f"requirements.txt:{line_num}: {line.strip()}")

    assert len(violations) == 0, (
        f"AI/ML compliance violation in requirements.txt!\n" + "\n".join(violations)
    )


def test_no_secret_keys_tracked_in_git():
    """Verify that git ls-files contains no tracked private keys (*_sk.bin or *.pem)."""
    try:
        res = subprocess.run(
            ["git", "ls-files", "*_sk.bin", "*.pem"],
            capture_output=True,
            text=True,
            check=True
        )
        tracked_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        assert len(tracked_files) == 0, f"Git tracks secret keys: {tracked_files}"
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        pytest.skip(f"Git command unavailable: {e}")
