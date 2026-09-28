"""
Простой раннер тестов для лексера и парсера.
Запуск: py tests/test_runner/run_tests.py
"""

import os
import sys
import subprocess

# корень проекта — на два уровня выше этого файла
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(ROOT, "tests")
CLI = os.path.join(ROOT, "cli.py")


def run_one(src_path, expected_path):
    """Запустить CLI на одном файле и сравнить с ожиданием."""
    # определяем команду по пути
    if "lexer" in src_path:
        cmd = "scan"
    elif "parser" in src_path:
        cmd = "tree"
    elif "semantic" in src_path:
        cmd = "check"
    elif "ir" in src_path:
        cmd = "ir"
    else:
        raise ValueError(f"unknown test stage: {src_path}")

    result = subprocess.run(
        [sys.executable, CLI, cmd, "--input", src_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # для invalid тестов ошибка идёт в stderr, поэтому склеиваем
    actual = (result.stdout + result.stderr).strip()

    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    return actual == expected, actual, expected


def main():
    total = 0
    passed = 0
    failed = []

    # проходим по всем подпапкам в tests/ (lexer, parser, ...)
    for stage in sorted(os.listdir(TESTS_DIR)):
        stage_dir = os.path.join(TESTS_DIR, stage)
        if not os.path.isdir(stage_dir):
            continue
        if stage in ("test_runner", "__pycache__"):
            continue

        for sub in ["valid", "invalid"]:
            folder = os.path.join(stage_dir, sub)
            if not os.path.isdir(folder):
                continue
            for name in sorted(os.listdir(folder)):
                if not name.endswith(".src"):
                    continue
                src = os.path.join(folder, name)
                exp = src[:-4] + ".expected"
                if not os.path.exists(exp):
                    print(f"SKIP {stage}/{sub}/{name} (no .expected)")
                    continue

                total += 1
                ok, actual, expected = run_one(src, exp)
                if ok:
                    passed += 1
                    print(f"OK   {stage}/{sub}/{name}")
                else:
                    failed.append((f"{stage}/{sub}", name, actual, expected))
                    print(f"FAIL {stage}/{sub}/{name}")

    print()
    print(f"passed: {passed}/{total}")

    if failed:
        print()
        print("=" * 60)
        for stage_sub, name, actual, expected in failed:
            print(f"--- {stage_sub}/{name} ---")
            print("expected:")
            print(expected)
            print("actual:")
            print(actual)
            print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())