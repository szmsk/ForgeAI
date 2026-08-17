from pathlib import Path

def create_demo_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "calculator.py").write_text('def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n', encoding="utf-8")
    (root / "test_calculator.py").write_text('''import unittest\nfrom calculator import add, multiply\n\nclass CalculatorTests(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2, 3), 5)\n    def test_multiply(self): self.assertEqual(multiply(3, 4), 12)\n    def test_negative_add(self): self.assertEqual(add(-2, 3), 1)\n\nif __name__ == "__main__": unittest.main()\n''', encoding="utf-8")
