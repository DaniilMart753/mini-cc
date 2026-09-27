"""
Простой раннер тестов для лексера.
Запуск: py tests/test_runner/run_tests.py
"""

import os
import sys
import subprocess

# корень проекта — на два уровня выше этого файла
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(ROOT, "tests", "lexer")
CLI = os.path.join(ROOT, "cli.py")


def run_one(src_path, expected_path):
    """Запустить лексер на одном файле и сравнить с ожиданием."""
    # запускаем CLI как подпроцесс
    result = subprocess.run(
        [sys.executable, CLI, "scan", "--input", src_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    actual = result.stdout.strip()

    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    return actual == expected, actual, expected


def main():
    total = 0
    passed = 0
    failed = []

    # проходим по valid и invalid
    for sub in ["valid", "invalid"]:
        folder = os.path.join(TESTS_DIR, sub)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".src"):
                continue
            src = os.path.join(folder, name)
            exp = src[:-4] + ".expected"
            if not os.path.exists(exp):
                print(f"SKIP {sub}/{name} (no .expected)")
                continue

            total += 1
            ok, actual, expected = run_one(src, exp)
            if ok:
                passed += 1
                print(f"OK   {sub}/{name}")
            else:
                failed.append((sub, name, actual, expected))
                print(f"FAIL {sub}/{name}")

    print()
    print(f"passed: {passed}/{total}")

    if failed:
        print()
        print("=" * 60)
        for sub, name, actual, expected in failed:
            print(f"--- {sub}/{name} ---")
            print("expected:")
            print(expected)
            print("actual:")
            print(actual)
            print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())