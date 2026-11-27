from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "official" / "problems"
TESTS = Path(__file__).resolve().parent / "countertests"

EXPECTED = {
    "4-1": ("2", "1"),
    "4-3": ("1", "2"),
    "5-1": ("1440", "0"),
    "5-2": ("1", "10"),
    "5-3": ("1410", "0"),
}


def run(source: Path, test_input: bytes) -> str:
    result = subprocess.run(
        [sys.executable, str(source)],
        input=test_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3,
        check=True,
    )
    return result.stdout.decode().strip()


def main() -> None:
    for test_path in sorted(TESTS.glob("*.in")):
        problem, wrong = test_path.stem.split("-")
        test_input = test_path.read_bytes()
        correct_output = run(PROBLEMS / problem / f"{problem}-correct.py", test_input)
        wrong_output = run(PROBLEMS / problem / f"{problem}-{wrong}.py", test_input)
        expected_correct, expected_wrong = EXPECTED[test_path.stem]

        assert correct_output == expected_correct, (test_path.name, correct_output)
        assert wrong_output == expected_wrong, (test_path.name, wrong_output)
        assert correct_output != wrong_output
        print(f"{test_path.name}: reference={correct_output}, wrong={wrong_output}")


if __name__ == "__main__":
    main()
